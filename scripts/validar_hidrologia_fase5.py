"""Validate watershed, stream network and TWI on a real WebODM DTM."""
import io
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from playwright.sync_api import expect, sync_playwright
from pyproj import Transformer
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject
from shapely.geometry import shape
from shapely.ops import transform

from backend.utils.raster_tiles import tile_bounds
from backend.utils.resource_access import data_path
from scripts.validar_publicacao_terreno_fase3 import API, PROJECT, login

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/validacao/hidrologia_fase5_2026-10-15'
DTM_NAME='Aukerman - DTM real para hidrologia'


def expected_rgba(values,valid,style):
    safe=np.nan_to_num(values)
    if style['kind']=='watershed': rgb=np.full((*values.shape,3),[37,99,235],dtype='uint8')
    else:
        palette=np.array([[180,83,9],[101,163,13],[3,105,161]])
        middle=(style['min']+style['max'])/2
        rgb=np.stack([np.interp(safe,[style['min'],middle,style['max']],palette[:,i]) for i in range(3)],axis=-1).astype('uint8')
    result=np.dstack((rgb,valid.astype('uint8')*255));result[~valid,:3]=0
    return result


def verify_tile(session,analysis):
    metadata=analysis['resultado'];style=metadata['style']
    if style['kind']=='watershed': lon=metadata['stats']['snapped_outlet']['lon'];lat=metadata['stats']['snapped_outlet']['lat']
    else: lon=(metadata['bbox_oeste']+metadata['bbox_leste'])/2;lat=(metadata['bbox_sul']+metadata['bbox_norte'])/2
    z=18;x=int((lon+180)/360*2**z);y=int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)
    grid=np.full((256,256),np.nan,dtype='float32')
    with rasterio.open(data_path(analysis['resultado_path'])) as ds:
        reproject(rasterio.band(ds,1),grid,src_transform=ds.transform,src_crs=ds.crs,src_nodata=ds.nodata,
                  dst_transform=from_bounds(*tile_bounds(z,x,y),256,256),dst_crs='EPSG:3857',dst_nodata=np.nan,
                  resampling=Resampling.nearest if style['kind']=='watershed' else Resampling.bilinear)
    valid=np.isfinite(grid);expected=expected_rgba(grid,valid,style)
    response=session.get(API+f"/analises/{analysis['id']}/tile/{z}/{x}/{y}.png",timeout=60);response.raise_for_status()
    actual=np.asarray(Image.open(io.BytesIO(response.content)));assert np.array_equal(actual,expected)
    Image.fromarray(actual).save(OUT/f"tile_{analysis['id']}.png")
    return {'rgba_exact':True,'opaque_pixels':int((actual[...,3]==255).sum()),'z':z,'x':x,'y':y}


def verify_watershed(analysis):
    stats=analysis['resultado']['stats']
    with rasterio.open(data_path(analysis['resultado_path'])) as ds:
        values=ds.read(1);count=int((values==1).sum());area=abs(ds.transform.a*ds.transform.e-ds.transform.b*ds.transform.d)*count
    assert count==stats['watershed_cells'] and abs(area-stats['area_m2'])<.001
    assert stats['snapped_outlet']['distance_m']<=80
    return {'cells':count,'area_m2':area,'snap_distance_m':stats['snapped_outlet']['distance_m']}


def verify_streams(analysis,source):
    metadata=analysis['resultado'];geojson=metadata['geojson'];stats=metadata['stats']
    with rasterio.open(data_path(source['caminho_arquivo'])) as ds: transformer=Transformer.from_crs(4326,ds.crs,always_xy=True)
    length=sum(transform(transformer.transform,shape(feature['geometry'])).length for feature in geojson['features'])
    assert len(geojson['features'])==stats['feature_count']
    assert abs(length-stats['total_length_m'])<.5,(length,stats['total_length_m'])
    return {'features':len(geojson['features']),'length_m_reprojected':length,'reported_length_m':stats['total_length_m']}


def main():
    OUT.mkdir(parents=True,exist_ok=True);result={'accepted':False,'errors':[],'screens':[],'checks':{}}
    session=login('phase1-1791391595@example.test','fase1-senha-segura')
    catalog=session.get(API+'/ortomapas',params={'projeto_id':62},timeout=30).json()['ortomapas'];source=next(item for item in catalog if item['nome']==DTM_NAME)
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True);page=browser.new_page(viewport={'width':1440,'height':1024});page.set_default_timeout(60000)
        page.on('pageerror',lambda error:result['errors'].append(str(error)))
        page.goto('http://127.0.0.1:5302',wait_until='networkidle');page.locator('input[type=email]').fill('phase1-1791391595@example.test');page.locator('input[type=password]').fill('fase1-senha-segura');page.get_by_role('button',name='Entrar',exact=True).click()
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='Aukerman - ortofoto ODM real').get_by_title('Visibilidade',exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        hydrology_tab=page.locator('.tools-panel').get_by_text('Hid',exact=True)
        for _ in range(5):
            if hydrology_tab.is_visible(): break
            page.locator('.tools-panel .p-tablist-next-button').click()
        expect(hydrology_tab).to_be_visible();hydrology_tab.click()

        def capture(name):
            page.locator('.tools-panel .p-button-loading').wait_for(state='hidden') if page.locator('.tools-panel .p-button-loading').count() else None
            page.locator('.p-select-overlay').last.wait_for(state='hidden') if page.locator('.p-select-overlay').count() else None
            page.wait_for_timeout(250)
            page.evaluate('()=>document.fonts.ready');page.wait_for_function("()=>[...document.querySelectorAll('.leaflet-tile-pane img')].every(i=>i.complete&&i.naturalWidth>0&&getComputedStyle(i).opacity==='1')")
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');page.screenshot(path=str(OUT/f'{name}.png'));result['screens'].append(f'{name}.png')
        def choose(label):
            page.locator('.tools-panel .p-select:visible').nth(1).click();page.get_by_role('option',name=label,exact=True).last.click()
        def wait_raster(aid): page.wait_for_function("id=>[...document.querySelectorAll('.leaflet-tile-pane img')].some(i=>i.src.includes('/analises/'+id+'/tile/')&&i.complete&&i.naturalWidth===256)",arg=aid)

        expect(page.locator('.tools-panel .p-select:visible').nth(0)).to_contain_text(DTM_NAME)
        page.get_by_role('button',name='Capturar do Mapa',exact=True).click();bounds=page.locator('.leaflet-container').bounding_box();page.mouse.click(bounds['x']+bounds['width']*.54,bounds['y']+bounds['height']*.55)
        inputs=page.locator('.tools-panel input[type=number]:visible');expect(inputs).to_have_count(3);inputs.nth(2).fill('80');capture('01_bacia_exutorio_parametros')
        with page.expect_response(lambda r:r.url.endswith('/tools/hydrology/watershed') and r.request.method=='POST',timeout=180000) as event: page.get_by_role('button',name='Executar',exact=True).click()
        response=event.value;assert response.status==200,response.text();watershed=response.json();watershed_analysis=watershed['analise'];result['watershed_id']=watershed_analysis['id'];wait_raster(watershed_analysis['id'])
        page.locator('.result-stats:visible').scroll_into_view_if_needed();capture('02_bacia_resultado')
        result['checks']['watershed']=verify_watershed(watershed_analysis);result['checks']['watershed_tile']=verify_tile(session,watershed_analysis)
        assert result['checks']['watershed_tile']['opaque_pixels']>0

        choose('Rede de Drenagem (Streams)');area=page.locator('.tools-panel input[type=number]:visible');area.fill('50');capture('03_drenagem_parametros')
        with page.expect_response(lambda r:r.url.endswith('/tools/hydrology/streams') and r.request.method=='POST',timeout=180000) as event: page.get_by_role('button',name='Executar',exact=True).click()
        response=event.value;assert response.status==200,response.text();streams=response.json();streams_analysis=streams['analise'];result['streams_id']=streams_analysis['id']
        page.locator('.result-stats:visible').scroll_into_view_if_needed();capture('04_drenagem_resultado')
        result['checks']['streams']=verify_streams(streams_analysis,source)

        choose('TWI - Indice Topografico')
        with page.expect_response(lambda r:r.url.endswith('/tools/hydrology/twi') and r.request.method=='POST',timeout=180000) as event: page.get_by_role('button',name='Executar',exact=True).click()
        response=event.value;assert response.status==200,response.text();twi=response.json();twi_analysis=twi['analise'];result['twi_id']=twi_analysis['id'];wait_raster(twi_analysis['id'])
        for layer in page.locator('.layer-item').all()[:-1]:
            hide=layer.get_by_title('Ocultar camada')
            if hide.count(): hide.click()
        page.locator('.result-stats:visible').scroll_into_view_if_needed();capture('05_twi_resultado')
        result['checks']['twi']={'min':twi['statistics']['band_1']['min'],'max':twi['statistics']['band_1']['max'],'mean':twi['statistics']['band_1']['mean'],'valid_pixels':twi['statistics']['band_1']['valid_pixels']}
        assert result['checks']['twi']['min']<result['checks']['twi']['mean']<result['checks']['twi']['max'];result['checks']['twi_tile']=verify_tile(session,twi_analysis)
        assert result['checks']['twi_tile']['opaque_pixels']>0

        page.reload(wait_until='networkidle');page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click();page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        row=page.locator(f'.result-item[data-analysis-id="{twi_analysis["id"]}"]');expect(row).to_have_count(1);row.click();wait_raster(twi_analysis['id']);capture('06_persistencia_hidrologia')
        browser.close()
    outsider=login('fase1-outsider@example.test','validacao-fase1-outsider')
    denied=outsider.post(API+'/tools/hydrology/twi',json={'dtm_path':source['caminho_arquivo'],'ortomapa_id':source['id'],'projeto_id':62,'output_name':'negado'},timeout=30)
    result['checks']['outsider_status']=denied.status_code;assert denied.status_code==403
    invalid=session.post(API+'/tools/hydrology/watershed',json={'dtm_path':source['caminho_arquivo'],'ortomapa_id':source['id'],'projeto_id':62,'output_name':'invalido','pour_point':{'lat':95,'lon':0}},timeout=30)
    result['checks']['invalid_outlet_status']=invalid.status_code;assert invalid.status_code==422
    assert not result['errors'];result['accepted']=True;(OUT/'resultado.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))


if __name__=='__main__': main()
