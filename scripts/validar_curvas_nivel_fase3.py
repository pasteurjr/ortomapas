"""Real UI contours, elevation checks, vector exports and project isolation."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import rasterio
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform
from playwright.sync_api import sync_playwright

from scripts.validar_publicacao_terreno_fase3 import login, PROJECT, API

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/validacao/curvas_nivel_fase3_2026-10-11'


def verify(analysis):
    data=analysis['resultado'];features=data['geojson']['features'];interval=data['stats']['interval_m']
    projected=Transformer.from_crs(4326,32617,always_xy=True)
    polygon=transform(projected.transform,shape(data['aoi']['geometry']))
    checked=0;errors=[]
    with rasterio.open(ROOT/'data/ortomapas/odm_2_dsm.tif') as ds:
        for feature in features:
            geom=transform(projected.transform,shape(feature['geometry']))
            assert polygon.buffer(.000001).covers(geom)
            elevation=feature['properties']['elevation_m']
            assert abs(elevation/interval-round(elevation/interval))<1e-8
            for x,y in list(geom.coords)[::max(1,len(geom.coords)//4)]:
                col,row=~ds.transform*(x,y);col-=.5;row-=.5
                if min(abs(col-round(col)),abs(row-round(row)))>1e-4:continue
                c,r=int(np.floor(col)),int(np.floor(row))
                if checked>=250:continue
                values=ds.read(1,window=rasterio.windows.Window(c,r,2,2)).astype(float)
                if values.shape!=(2,2) or (values==ds.nodata).any():continue
                fc,fr=col-c,row-r
                expected=(values[0,0]*(1-fc)+values[0,1]*fc)*(1-fr)+(values[1,0]*(1-fc)+values[1,1]*fc)*fr
                errors.append(abs(elevation-expected));checked+=1
    assert checked>=20 and max(errors)<.001,(checked,max(errors,default=0))
    assert len(features)==data['stats']['feature_count']
    return {'features':len(features),'checked_vertices':checked,'max_elevation_error_m':max(errors),
            'all_lines_inside_aoi':True,'interval_m':interval,'major_count':data['stats']['major_count']}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={'accepted':False,'errors':[],'screens':[],'analyses':[],'downloads':{}}
    (OUT/'resultado.json').write_text(json.dumps(result))
    session=login('phase1-1791391595@example.test','fase1-senha-segura')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1024});page.set_default_timeout(60000)
        page.on('pageerror',lambda error:result['errors'].append(str(error)))
        page.goto('http://127.0.0.1:5302',wait_until='networkidle')
        page.locator('input[type=email]').fill('phase1-1791391595@example.test')
        page.locator('input[type=password]').fill('fase1-senha-segura')
        page.get_by_role('button',name='Entrar',exact=True).click()
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='Aukerman - ortofoto ODM real').get_by_title('Visibilidade',exact=True).click()
        page.wait_for_function("()=>{const t=[...document.querySelectorAll('.leaflet-tile-pane img')].filter(i=>i.src.includes('/ortomapas/30/tile/'));return t.length>0&&t.every(i=>i.complete&&i.naturalWidth===256&&getComputedStyle(i).opacity==='1')}")
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        page.locator('.tools-panel').get_by_text('Ter',exact=True).click()
        page.locator('.tools-panel .p-select:visible').nth(1).click();page.get_by_role('option',name='Curvas de Nivel (Contours)',exact=True).click()
        page.locator('.terrain-aoi input:visible').check();page.get_by_title('Desenhar area de analise',exact=True).click()
        page.locator('.leaflet-mouse-marker').wait_for(state='attached')
        box=page.locator('.leaflet-container').bounding_box();cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
        points=[(cx-65,cy-50),(cx+75,cy-25),(cx+55,cy+65),(cx-40,cy+45)]
        for n,(x,y) in enumerate(points):
            page.mouse.click(x,y,delay=100);page.wait_for_timeout(100)
            page.wait_for_function('n=>document.querySelectorAll(".leaflet-editing-icon").length===n',arg=n+1)
        page.mouse.click(*points[0]);page.get_by_text('Area selecionada',exact=True).wait_for()
        def capture(name):
            page.evaluate('()=>document.fonts.ready')
            page.wait_for_function("()=>!document.querySelector('.leaflet-zoom-anim')&&[...document.querySelectorAll('.leaflet-tile-loaded')].every(i=>i.complete&&getComputedStyle(i).opacity==='1')")
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            page.screenshot(path=str(OUT/(name+'.png')));result['screens'].append(name+'.png')
        def wait_lines(analysis):
            expected=analysis['resultado']['stats']['feature_count']
            page.wait_for_function("n=>document.querySelectorAll('.leaflet-overlay-pane path[stroke=\"#d96a19\"],.leaflet-overlay-pane path[stroke=\"#a62626\"]').length===n",arg=expected)
        def generate(interval):
            page.locator('.tools-panel input[type=number]:visible').fill(str(interval))
            with page.expect_response(lambda r:r.url.endswith('/tools/contours') and r.request.method=='POST',timeout=180000) as response:
                page.get_by_role('button',name='Gerar Analise',exact=True).click()
            r=response.value;return r
        page.locator('.tools-panel .tool-form:visible').scroll_into_view_if_needed();capture('01_area_e_parametros')
        for interval in [2,1]:
            r=generate(interval);assert r.status==200,r.text()
            analysis=r.json()['analise'];assert analysis['projeto_id']==62 and analysis['ortomapa_id']==34
            wait_lines(analysis)
            page.locator('.tools-panel .tool-form:visible').scroll_into_view_if_needed()
            check=verify(analysis);result['analyses'].append({'analysis':analysis,'verification':check})
            print('Curvas #'+str(analysis['id'])+' '+json.dumps(check),flush=True)
            capture('curvas_'+str(interval)+'m')
            if interval==2:
                page.locator('.layer-control-item').filter(has_text=analysis['nome']).get_by_title('Remover camada',exact=True).click()
        last=result['analyses'][-1]['analysis'];aid=last['id']
        assert result['analyses'][1]['verification']['features']>result['analyses'][0]['verification']['features']
        position=page.evaluate("()=>{const p=document.querySelector('.leaflet-overlay-pane path[stroke=\"#a62626\"]');const pt=p.getPointAtLength(p.getTotalLength()/2).matrixTransform(p.getScreenCTM());return {x:pt.x,y:pt.y}}")
        page.mouse.move(position['x'],position['y'])
        page.locator('.leaflet-tooltip').filter(has_text='m').wait_for()
        result['tooltip']=page.locator('.leaflet-tooltip').inner_text();capture('04_inspecao_cota')
        control=page.locator('.layer-control-item').filter(has_text=last['nome'])
        for format in ['GeoJSON','KML']:
            with page.expect_download() as download:control.get_by_title('Baixar '+format,exact=True).click()
            file=Path('/tmp')/('curvas_'+str(aid)+'.'+format.lower());download.value.save_as(str(file))
            if format=='GeoJSON':assert json.loads(file.read_text())==last['resultado']['geojson']
            else:
                xml=ET.parse(file);ns={'k':'http://www.opengis.net/kml/2.2'}
                placemarks=xml.findall('.//k:Placemark',ns)
                assert len(placemarks)==len(last['resultado']['geojson']['features'])
                for node,feature in zip(placemarks,last['resultado']['geojson']['features']):
                    actual=[list(map(float,p.split(',')))[:2] for p in node.find('.//k:coordinates',ns).text.split()]
                    assert np.allclose(actual,feature['geometry']['coordinates'],atol=1e-12,rtol=0)
                    assert float(node.find('.//k:Data[@name="elevation_m"]/k:value',ns).text)==feature['properties']['elevation_m']
            result['downloads'][format]={'bytes':file.stat().st_size,'features':len(last['resultado']['geojson']['features'])}
        page.reload(wait_until='networkidle')
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        row=page.locator(f'.result-item[data-analysis-id="{aid}"]');row.click();wait_lines(last)
        assert not page.locator('.leaflet-tile-pane img[src*="/api/ortomapas/"]').count()
        page.locator('.stats-panel').scroll_into_view_if_needed();capture('05_reabertura_catalogo')
        with page.expect_download() as download:row.get_by_title('Baixar resultado GeoJSON',exact=True).click()
        file=Path('/tmp')/f'curvas_original_{aid}.geojson';download.value.save_as(str(file))
        def digest(path):
            with open(path,'rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
        assert digest(file)==digest(last['resultado_path'])
        result['downloads']['original']={'bytes':file.stat().st_size,'sha256':digest(file)}
        page.locator('.tools-panel').get_by_text('Ter',exact=True).click()
        page.locator('.tools-panel .p-select:visible').nth(1).click();page.get_by_role('option',name='Curvas de Nivel (Contours)',exact=True).click()
        page.locator('.terrain-aoi input:visible').check()
        r=generate(1000);assert r.status==422,r.text()
        page.locator('.terrain-error').wait_for();page.locator('.tools-panel .tool-form:visible').scroll_into_view_if_needed();capture('06_intervalo_sem_curvas')
        result['empty_interval_status']=r.status
        browser.close()
    outsider=login('fase1-outsider@example.test','validacao-fase1-outsider')
    result['outsider_result_status']=outsider.get(API+f'/analises/{aid}/resultado',timeout=30).status_code
    assert result['outsider_result_status']==403
    result['vector_tile_status']=session.get(API+f'/analises/{aid}/tile-access',timeout=30).status_code
    assert result['vector_tile_status']==404
    assert not result['errors'];result['accepted']=True
    # Keep provenance and AOI in Git; the full contour geometry stays in the published file.
    manifest={**result,'analyses':[{'analysis':{**{k:v for k,v in item['analysis'].items() if k!='resultado_json'},'resultado':{
        k:v for k,v in item['analysis']['resultado'].items() if k!='geojson'}},
        'verification':item['verification']} for item in result['analyses']]}
    (OUT/'resultado.json').write_text(json.dumps(manifest,indent=2))
    print('Curvas aceitas; '+str(len(result['screens']))+' capturas',flush=True)


if __name__=='__main__':main()
