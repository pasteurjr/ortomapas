"""Draw a real polygon in the UI and independently verify masked derivatives."""
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from pyproj import Transformer
from shapely import contains_xy
from shapely.geometry import shape
from shapely.ops import transform
from playwright.sync_api import sync_playwright

from scripts.validar_publicacao_terreno_fase3 import login, PROJECT, API

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/validacao/aoi_terreno_fase3_2026-10-11'


def verify(analysis):
    with rasterio.open(ROOT/'data/ortomapas/odm_2_dsm.tif') as source, rasterio.open(analysis['resultado_path']) as output:
        actual=output.read(1,masked=True)
        assert output.crs==source.crs and output.res==source.res
        assert output.width<source.width and output.height<source.height
        col,row=~source.transform*(output.transform.c,output.transform.f)
        col,row=round(col),round(row)
        assert col>0 and row>0 and col+output.width<source.width and row+output.height<source.height
        dem=source.read(1,window=Window(col-1,row-1,output.width+2,output.height+2),masked=True).astype(float).filled(np.nan)
        dr,dc=np.gradient(dem)
        east=(dc/source.transform.a)[1:-1,1:-1];north=(dr/source.transform.e)[1:-1,1:-1]
        kind=analysis['resultado']['provenance']['operation']
        if kind=='slope': expected=np.degrees(np.arctan(np.hypot(east,north)))
        elif kind=='aspect':
            expected=(np.degrees(np.arctan2(-east,-north))+360)%360
            expected[np.hypot(east,north)<=1e-12]=np.nan
        else:
            az,alt=np.radians([315,45])
            expected=np.clip((-east*np.sin(az)*np.cos(alt)-north*np.cos(az)*np.cos(alt)+np.sin(alt))/np.sqrt(1+east**2+north**2),0,1)*255
        rr,cc=np.indices(actual.shape)
        x=output.transform.c+(cc+.5)*output.transform.a
        y=output.transform.f+(rr+.5)*output.transform.e
        polygon=transform(Transformer.from_crs(4326,output.crs,always_xy=True).transform,shape(analysis['resultado']['aoi']['geometry']))
        inside=contains_xy(polygon,x,y)
        valid=inside & np.isfinite(expected) & np.isfinite(dem[1:-1,1:-1])
        assert np.array_equal(~np.ma.getmaskarray(actual),valid)
        error=float(np.max(np.abs(actual.data[valid]-expected[valid])))
        assert error<.0001,error
        stats=analysis['resultado']['stats']
        assert stats['valid_pixels']==int(valid.sum())
        assert abs(stats['mean']-float(expected[valid].mean()))<.0001
        assert np.count_nonzero(~inside)>0
        return {'valid_pixels':int(valid.sum()),'outside_pixels':int((~inside).sum()),'max_error':error,
                'mean':stats['mean'],'width':output.width,'height':output.height,
                'area_m2':analysis['resultado']['aoi']['area_m2'],
                'valid_area_m2':analysis['resultado']['aoi']['valid_area_m2'], 'mask_exact':True}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={'accepted':False,'errors':[],'screens':[],'analyses':[]}
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
        print('Login enviado',flush=True)
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='Aukerman - ortofoto ODM real').get_by_title('Visibilidade',exact=True).click()
        page.wait_for_function("()=>[...document.querySelectorAll('.leaflet-tile-pane img')].some(i=>i.src.includes('/ortomapas/30/tile/')&&i.complete&&i.naturalWidth===256)")
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        page.locator('.tools-panel').get_by_text('Ter',exact=True).click()
        page.locator('.terrain-aoi input[type=checkbox]').check()
        print('AOI habilitada',flush=True)
        assert page.get_by_role('button',name='Gerar Analise',exact=True).is_disabled()
        page.get_by_title('Desenhar area de analise',exact=True).click()
        page.locator('.leaflet-mouse-marker').wait_for(state='attached')
        box=page.locator('.leaflet-container').bounding_box()
        cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
        points=[(cx-65,cy-50),(cx+75,cy-25),(cx+55,cy+65),(cx-40,cy+45)]
        for index,(x,y) in enumerate(points):
            # Leaflet Draw debounces mouse/touch events for 50 ms; use human clicks.
            page.mouse.click(x,y,delay=100)
            page.wait_for_timeout(100)  # Debounce starts on mouseup, not mousedown.
            print('Vertice '+str(index+1)+' marcadores '+str(page.locator('.leaflet-editing-icon').count()),flush=True)
            try:
                page.wait_for_function('n=>document.querySelectorAll(".leaflet-editing-icon").length===n',arg=index+1,timeout=10000)
            except Exception:
                page.screenshot(path=str(OUT/'diagnostico_desenho.png'))
                raise
        page.mouse.click(*points[0])
        page.screenshot(path=str(OUT/'diagnostico_desenho.png'))
        page.get_by_text('Area selecionada',exact=True).wait_for()
        def capture(name):
            page.evaluate('()=>document.fonts.ready')
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            page.screenshot(path=str(OUT/(name+'.png')));result['screens'].append(name+'.png')
        capture('01_area_desenhada')
        for kind,label in [('slope','Declividade (Slope)'),('aspect','Aspecto (Aspect)'),('hillshade','Sombreamento (Hillshade)')]:
            page.locator('.tools-panel .p-select:visible').nth(1).click();page.get_by_role('option',name=label,exact=True).click()
            with page.expect_response(lambda r:r.url.endswith('/tools/'+kind) and r.request.method=='POST') as response:
                page.get_by_role('button',name='Gerar Analise',exact=True).click()
            r=response.value;assert r.status==200,r.text()
            analysis=r.json()['analise'];aid=analysis['id']
            assert analysis['projeto_id']==62 and analysis['resultado']['provenance']['scope']=='aoi'
            page.wait_for_function("id=>{const t=[...document.querySelectorAll('.leaflet-tile-pane img')].filter(i=>i.src.includes('/analises/'+id+'/tile/'));return t.length>0&&t.every(i=>i.complete&&i.naturalWidth===256&&getComputedStyle(i).opacity==='1')}",arg=aid)
            page.locator('.tools-panel .tool-form:visible').scroll_into_view_if_needed()
            verification=verify(analysis)
            result['analyses'].append({'analysis':analysis,'verification':verification})
            print(kind+' #'+str(aid)+' '+json.dumps(verification),flush=True)
            capture(kind+'_recortado')
            page.locator('.layer-control-item').filter(has_text=analysis['nome']).get_by_title('Remover camada',exact=True).click()
        last=result['analyses'][0]['analysis'];aid=last['id']
        page.reload(wait_until='networkidle')
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        row=page.locator(f'.result-item[data-analysis-id="{aid}"]');row.click()
        page.wait_for_function("id=>{const t=[...document.querySelectorAll('.leaflet-tile-pane img')].filter(i=>i.src.includes('/analises/'+id+'/tile/'));return t.length>0&&t.every(i=>i.complete&&i.naturalWidth===256&&getComputedStyle(i).opacity==='1')}",arg=aid)
        assert page.locator('.leaflet-overlay-pane path').count()>0
        assert not page.locator('.leaflet-tile-pane img[src*="/api/ortomapas/"]').count()
        page.locator('.stats-panel').scroll_into_view_if_needed()
        capture('05_reabertura_area_e_estatisticas')
        with page.expect_download() as download: row.get_by_title('Baixar resultado GeoTIFF',exact=True).click()
        path=Path('/tmp')/f'aoi_analise_{aid}.tif';download.value.save_as(str(path))
        def digest(file):
            with open(file,'rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
        assert digest(path)==digest(last['resultado_path'])
        result['download']={'bytes':path.stat().st_size,'sha256':digest(path)}
        page.locator('.tools-panel').get_by_text('Ter',exact=True).click()
        page.locator('.terrain-aoi input[type=checkbox]').check()
        page.get_by_title('Limpar area de analise',exact=True).click()
        assert page.get_by_role('button',name='Gerar Analise',exact=True).is_disabled()
        page.get_by_text('Sem area',exact=True).wait_for()
        page.locator('.tools-panel .tool-form:visible').scroll_into_view_if_needed()
        capture('06_area_limpa_execucao_bloqueada')
        result['clear_blocks_generation']=True
        browser.close()
    response=session.post(API+'/tools/slope',json={'input_path':'ortomapas/odm_2_dsm.tif','output_name':'invalid_aoi','ortomapa_id':34,'projeto_id':62,
                                                 'aoi':{'type':'Polygon','coordinates':[[[0,0],[1,0],[1,1],[0,0]]]}},timeout=30)
    assert response.status_code==422,response.text
    result['outside_aoi_status']=response.status_code
    assert not result['errors'];result['accepted']=True
    (OUT/'resultado.json').write_text(json.dumps(result,indent=2))
    print('AOI aceita; '+str(len(result['screens']))+' capturas',flush=True)


if __name__=='__main__':main()
