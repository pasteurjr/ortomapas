"""Validate visible-RGB vegetation indices and unsupervised KMeans end to end."""
import io
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from playwright.sync_api import expect, sync_playwright
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject

from backend.utils.raster_tiles import tile_bounds
from backend.utils.resource_access import data_path
from scripts.validar_publicacao_terreno_fase3 import API, PROJECT, login

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/validacao/vegetacao_classificacao_fase3_2026-10-13'
SOURCE_NAME='Aukerman - ortofoto ODM real'


def expected_color(values,valid,style):
    safe=np.nan_to_num(values)
    if style['kind']=='vegetation':
        palette=np.array([[140,81,10],[246,232,195],[27,120,55]])
        stops=[style['min'],(style['min']+style['max'])/2,style['max']]
        rgb=np.stack([np.interp(safe,stops,palette[:,i]) for i in range(3)],axis=-1).astype('uint8')
    else:
        palette=np.array([[int(c[i:i+2],16) for i in (1,3,5)] for c in style['colors']],dtype='uint8')
        rgb=palette[np.clip(np.rint(safe).astype(int)-1,0,len(palette)-1)]
    rgba=np.dstack((rgb,valid.astype('uint8')*255));rgba[~valid,:3]=0
    return rgba


def verify_tile(session,analysis):
    metadata=analysis['resultado'];style=metadata['style'];z=18
    lon=(metadata['bbox_oeste']+metadata['bbox_leste'])/2
    lat=(metadata['bbox_sul']+metadata['bbox_norte'])/2
    x=int((lon+180)/360*2**z);y=int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)
    grid=np.full((256,256),np.nan,dtype='float32')
    with rasterio.open(data_path(analysis['resultado_path'])) as ds:
        reproject(rasterio.band(ds,1),grid,src_transform=ds.transform,src_crs=ds.crs,src_nodata=ds.nodata,
                  dst_transform=from_bounds(*tile_bounds(z,x,y),256,256),dst_crs='EPSG:3857',dst_nodata=np.nan,
                  resampling=Resampling.nearest if style['kind']=='classification' else Resampling.bilinear)
    valid=np.isfinite(grid);expected=expected_color(grid,valid,style)
    response=session.get(API+f"/analises/{analysis['id']}/tile/{z}/{x}/{y}.png",timeout=60)
    response.raise_for_status();actual=np.asarray(Image.open(io.BytesIO(response.content)))
    assert np.array_equal(actual,expected)
    Image.fromarray(actual).save(OUT/f"tile_{analysis['id']}.png")
    return {'z':z,'x':x,'y':y,'rgba_exact':True,'opaque_pixels':int((actual[...,3]==255).sum())}


def verify_vari(source,analysis):
    with rasterio.open(data_path(source['caminho_arquivo'])) as src,rasterio.open(data_path(analysis['resultado_path'])) as out:
        bands=np.empty((3,out.height,out.width),dtype='float64')
        for band in range(3):
            reproject(rasterio.band(src,band+1),bands[band],src_transform=src.transform,src_crs=src.crs,
                      src_nodata=src.nodata,dst_transform=out.transform,dst_crs=out.crs,dst_nodata=np.nan,
                      resampling=Resampling.nearest)
        actual=out.read(1,masked=True);valid=~np.ma.getmaskarray(actual)&np.isfinite(actual.data)
        r,g,b=bands;denominator=g+r-b;denominator[np.abs(denominator)<1e-10]=1e-10
        expected=(g-r)/denominator
        error=float(np.max(np.abs(actual.data[valid]-expected[valid])))
        values=actual.compressed();stats=analysis['resultado']['stats']
        assert error<0.00005
        assert stats['valid_pixels']==len(values)
        for key,value in [('min',values.min()),('max',values.max()),('mean',values.mean())]:
            assert abs(stats[key]-value)<0.00005,(key,stats[key],value)
    return {'valid_pixels':int(len(values)),'max_formula_error':error,'min':float(values.min()),
            'max':float(values.max()),'mean':float(values.mean())}


def verify_classification(analysis):
    metadata=analysis['resultado'];clusters=metadata['classes']
    with rasterio.open(data_path(analysis['resultado_path'])) as ds:
        labels=ds.read(1,masked=True);values=labels.compressed();pixel_area=abs(ds.transform.a*ds.transform.e-ds.transform.b*ds.transform.d)
    assert set(np.unique(values))==set(range(1,len(clusters)+1))
    for cluster in clusters:
        count=int((values==int(cluster['nome'].split()[-1])).sum())
        assert count==cluster['pixel_count']
        assert abs(cluster['area']-count*pixel_area)<.011
        assert abs(cluster['percentual']-count*100/len(values))<.00011
    assert abs(sum(item['percentual'] for item in clusters)-100)<.001
    assert metadata['provenance']['semantic_labels'] is False
    return {'groups':len(clusters),'valid_pixels':int(len(values)),'percent_sum':sum(x['percentual'] for x in clusters),
            'labels':sorted(map(int,np.unique(values)))}


def select_option(page,selector,label):
    selector.click();page.get_by_role('option',name=label,exact=True).last.click()


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={'accepted':False,'errors':[],'screens':[],'checks':{}}
    session=login('phase1-1791391595@example.test','fase1-senha-segura')
    catalog=session.get(API+'/ortomapas',params={'projeto_id':62},timeout=30).json()['ortomapas']
    source=next(item for item in catalog if item['nome']==SOURCE_NAME)
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1024});page.set_default_timeout(60000)
        page.on('pageerror',lambda error:result['errors'].append(str(error)))
        page.goto('http://127.0.0.1:5302',wait_until='networkidle')
        page.locator('input[type=email]').fill('phase1-1791391595@example.test')
        page.locator('input[type=password]').fill('fase1-senha-segura')
        page.get_by_role('button',name='Entrar',exact=True).click()
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.ortomapa-card').filter(has_text=SOURCE_NAME).get_by_title('Visibilidade',exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()

        def capture(name):
            page.evaluate('()=>document.fonts.ready')
            page.wait_for_function("()=>[...document.querySelectorAll('.leaflet-tile-pane img')].every(i=>i.complete&&i.naturalWidth>0&&getComputedStyle(i).opacity==='1')")
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            page.screenshot(path=str(OUT/f'{name}.png'),full_page=False);result['screens'].append(f'{name}.png')

        page.locator('.tools-panel').get_by_text('Veg',exact=True).click()
        expect(page.locator('.tools-panel .p-select:visible').nth(0)).to_contain_text(SOURCE_NAME)
        page.locator('.tools-panel .terrain-aoi input:visible').check()
        button=page.get_by_role('button',name='Calcular Indice',exact=True);expect(button).to_be_disabled()
        page.get_by_title('Desenhar area do indice',exact=True).click()
        page.locator('.leaflet-mouse-marker').wait_for(state='attached')
        bounds=page.locator('.leaflet-container').bounding_box();cx=bounds['x']+bounds['width']/2;cy=bounds['y']+bounds['height']/2
        points=[(cx-90,cy-70),(cx+90,cy-70),(cx+90,cy+70),(cx-90,cy+70)]
        for number,point in enumerate(points):
            page.mouse.click(*point,delay=80);page.wait_for_timeout(80)
            page.wait_for_function('n=>document.querySelectorAll(".leaflet-editing-icon").length===n',arg=number+1)
        page.mouse.click(*points[0]);page.get_by_text('Area selecionada',exact=True).wait_for();expect(button).to_be_enabled()
        capture('01_vari_parametros_aoi')
        with page.expect_response(lambda r:r.url.endswith('/tools/vegetation') and r.request.method=='POST',timeout=180000) as event:
            button.click()
        response=event.value;assert response.status==200,response.text();vegetation=response.json()['analise']
        result['vegetation_id']=vegetation['id']
        page.wait_for_function("id=>[...document.querySelectorAll('.leaflet-tile-pane img')].some(i=>i.src.includes('/analises/'+id+'/tile/')&&i.complete&&i.naturalWidth===256)",arg=vegetation['id'])
        page.locator('.result-stats:visible').scroll_into_view_if_needed();capture('02_vari_resultado_mapa')
        result['checks']['vari']=verify_vari(source,vegetation);result['checks']['vari_tile']=verify_tile(session,vegetation)

        page.locator('.tools-panel').get_by_text('Cls',exact=True).click()
        expect(page.locator('.tools-panel .p-select:visible').nth(0)).to_contain_text(SOURCE_NAME)
        number=page.locator('.tools-panel input[type=number]:visible');number.fill('5')
        page.locator('.tools-panel .terrain-aoi input:visible').check()
        capture('03_kmeans_parametros_mesma_aoi')
        classify=page.get_by_role('button',name='Gerar Grupos',exact=True);expect(classify).to_be_enabled()
        with page.expect_response(lambda r:r.url.endswith('/tools/classify') and r.request.method=='POST',timeout=180000) as event:
            classify.click()
        response=event.value;assert response.status==200,response.text();payload=response.json();classification=payload['analise']
        result['classification_id']=classification['id']
        page.wait_for_function("id=>[...document.querySelectorAll('.leaflet-tile-pane img')].some(i=>i.src.includes('/analises/'+id+'/tile/')&&i.complete&&i.naturalWidth===256)",arg=classification['id'])
        page.locator('.class-result').scroll_into_view_if_needed();capture('04_kmeans_resultado_mapa_grupos')
        result['checks']['classification']=verify_classification(classification)
        result['checks']['classification_tile']=verify_tile(session,classification)

        page.reload(wait_until='networkidle')
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        row=page.locator(f'.result-item[data-analysis-id="{classification["id"]}"]');expect(row).to_have_count(1);row.click()
        page.wait_for_function("id=>[...document.querySelectorAll('.leaflet-tile-pane img')].some(i=>i.src.includes('/analises/'+id+'/tile/')&&i.complete)",arg=classification['id'])
        capture('05_persistencia_catalogo_classificacao')
        browser.close()

    body={'ortomapa_path':source['caminho_arquivo'],'ortomapa_id':source['id'],'projeto_id':62,
          'output_name':'validacao_invalida','index_name':'NDVI'}
    result['checks']['ndvi_without_nir_status']=session.post(API+'/tools/vegetation',json={
        'input_path':source['caminho_arquivo'],'ortomapa_id':source['id'],'projeto_id':62,
        'output_name':'ndvi_invalido','index_name':'NDVI'},timeout=30).status_code
    assert result['checks']['ndvi_without_nir_status']==422
    dsm=next(item for item in catalog if item['tipo'].lower()=='dsm')
    result['checks']['dsm_as_rgb_status']=session.post(API+'/tools/classify',json={**body,
        'ortomapa_path':dsm['caminho_arquivo'],'ortomapa_id':dsm['id'],'algorithm':'kmeans','n_clusters':5},timeout=30).status_code
    assert result['checks']['dsm_as_rgb_status']==422
    outsider=login('fase1-outsider@example.test','validacao-fase1-outsider')
    result['checks']['outsider_status']=outsider.post(API+'/tools/classify',json={**body,'algorithm':'kmeans','n_clusters':5},timeout=30).status_code
    assert result['checks']['outsider_status']==403
    assert not result['errors'];result['accepted']=True
    (OUT/'resultado.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    main()
