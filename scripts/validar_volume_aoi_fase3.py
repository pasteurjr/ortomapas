"""Real volume UI with independent raster, volume, tile and file comparisons."""
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
from pyproj import Transformer
from shapely import contains_xy
from shapely.geometry import shape
from shapely.ops import transform
from PIL import Image
from playwright.sync_api import sync_playwright, expect

from scripts.validar_publicacao_terreno_fase3 import login, PROJECT, API
from backend.utils.raster_tiles import tile_bounds

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/validacao/volume_aoi_fase3_2026-10-12'


def verify(analysis, session):
    data=analysis['resultado'];reference=data['provenance']['reference_elevation_m']
    with rasterio.open(ROOT/'data/ortomapas/odm_2_dsm.tif') as src, rasterio.open(analysis['resultado_path']) as dst:
        assert dst.crs==src.crs and dst.res==src.res
        col,row=~src.transform*(dst.transform.c,dst.transform.f)
        values=src.read(1,window=Window(round(col),round(row),dst.width,dst.height),masked=True).astype(float)
        rr,cc=np.indices(values.shape)
        x=dst.transform.c+(cc+.5)*dst.transform.a;y=dst.transform.f+(rr+.5)*dst.transform.e
        polygon=transform(Transformer.from_crs(4326,dst.crs,always_xy=True).transform,shape(data['aoi']['geometry']))
        valid=contains_xy(polygon,x,y)&~np.ma.getmaskarray(values)&np.isfinite(values.data)
        expected=values.data-reference
        actual=dst.read(1,masked=True)
        assert np.array_equal(~np.ma.getmaskarray(actual),valid)
        error=float(np.max(np.abs(actual.data[valid]-expected[valid])));assert error<.00001
        pixel_area=abs(src.transform.a*src.transform.e-src.transform.b*src.transform.d)
        cut=float(np.maximum(expected[valid],0).sum()*pixel_area)
        fill=float(np.maximum(-expected[valid],0).sum()*pixel_area)
        for key,value in [('volume_above_m3',cut),('volume_below_m3',fill),('net_volume_m3',cut-fill)]:
            assert abs(data['stats'][key]-value)<.011,(key,data['stats'][key],value)
        assert abs(data['stats']['valid_area_m2']-valid.sum()*pixel_area)<.000001
        expected_masked=np.where(valid,expected,np.nan).astype('float32')
        center=shape(data['aoi']['geometry']).centroid;z=18;n=2**z
        tx=int((center.x+180)/360*n)
        ty=int((1-math.asinh(math.tan(math.radians(center.y)))/math.pi)/2*n)
        tile=np.full((256,256),np.nan,dtype='float32')
        reproject(expected_masked,tile,src_transform=dst.transform,src_crs=dst.crs,src_nodata=np.nan,
                  dst_transform=from_bounds(*tile_bounds(z,tx,ty),256,256),dst_crs=3857,dst_nodata=np.nan,resampling=Resampling.nearest)
    mask=np.isfinite(tile);style=data['style'];palette=np.array([[33,102,172],[247,247,247],[178,24,43]])
    rgb=np.stack([np.interp(np.nan_to_num(tile),[style['min'],0,style['max']],palette[:,i]) for i in range(3)],axis=-1).astype('uint8')
    rgba=np.dstack((rgb,mask.astype('uint8')*255));rgba[~mask,:3]=0
    response=session.get(API+f"/analises/{analysis['id']}/tile/{z}/{tx}/{ty}.png",timeout=60);response.raise_for_status()
    obtained=np.asarray(Image.open(io.BytesIO(response.content)))
    assert np.array_equal(obtained,rgba)
    assert mask.any() and (~mask).any()
    Image.fromarray(obtained).save(OUT/f"tile_{analysis['id']}.png")
    return {'reference_m':reference,'cut_m3':cut,'fill_m3':fill,'net_m3':cut-fill,
            'valid_pixels':int(valid.sum()),'valid_area_m2':float(valid.sum()*pixel_area),
            'mask_exact':True,'max_raster_error_m':error,'tile_rgba_exact':True,
            'tile_valid_pixels':int(mask.sum()),'tile_transparent_pixels':int((~mask).sum())}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={'accepted':False,'errors':[],'screens':[],'analyses':[]}
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
        page.locator('.tools-panel').get_by_text('Vol',exact=True).click()
        assert page.get_by_role('button',name='Calcular Volume',exact=True).is_disabled()
        page.locator('.tools-panel input[type=number]:visible').fill('241')
        expect(page.get_by_role('button',name='Calcular Volume',exact=True)).to_be_enabled()
        page.locator('.terrain-aoi input:visible').check()
        assert page.get_by_role('button',name='Calcular Volume',exact=True).is_disabled()
        page.get_by_title('Desenhar area de volume',exact=True).click()
        page.locator('.leaflet-mouse-marker').wait_for(state='attached')
        box=page.locator('.leaflet-container').bounding_box();cx=box['x']+box['width']/2;cy=box['y']+box['height']/2
        points=[(cx-65,cy-50),(cx+75,cy-25),(cx+55,cy+65),(cx-40,cy+45)]
        for n,(x,y) in enumerate(points):
            page.mouse.click(x,y,delay=100);page.wait_for_timeout(100)
            page.wait_for_function('n=>document.querySelectorAll(".leaflet-editing-icon").length===n',arg=n+1)
        page.mouse.click(*points[0]);page.get_by_text('Area selecionada',exact=True).wait_for()
        def capture(name):
            if page.locator('.tools-panel input[type=number]:visible').count():
                expect(page.locator('.tools-panel input[type=number]:visible')).to_be_enabled()
            page.evaluate('()=>document.fonts.ready')
            page.wait_for_function("()=>!document.querySelector('.leaflet-zoom-anim')&&[...document.querySelectorAll('.leaflet-tile-loaded')].every(i=>i.complete&&getComputedStyle(i).opacity==='1')")
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            page.screenshot(path=str(OUT/(name+'.png')));result['screens'].append(name+'.png')
        def wait_tiles(aid):
            page.wait_for_function("id=>{const t=[...document.querySelectorAll('.leaflet-tile-pane img')].filter(i=>i.src.includes('/analises/'+id+'/tile/'));return t.length>0&&t.every(i=>i.complete&&i.naturalWidth===256&&getComputedStyle(i).opacity==='1')}",arg=aid)
        page.locator('.tools-panel input[type=number]:visible').fill('241')
        page.locator('.tools-panel .tool-form:visible').scroll_into_view_if_needed();capture('01_area_e_cota')
        for reference in [241,242]:
            page.locator('.tools-panel input[type=number]:visible').fill(str(reference))
            if reference==242:assert not page.locator('.volume-result').count()
            with page.expect_response(lambda r:r.url.endswith('/tools/volume') and r.request.method=='POST',timeout=180000) as response:
                page.get_by_role('button',name='Calcular Volume',exact=True).click()
            r=response.value;assert r.status==200,r.text();analysis=r.json()['analise']
            assert analysis['projeto_id']==62 and analysis['ortomapa_id']==34 and analysis['tipo_analise']=='volume'
            wait_tiles(analysis['id']);page.locator('.volume-result').scroll_into_view_if_needed()
            check=verify(analysis,session);result['analyses'].append({'analysis':{k:v for k,v in analysis.items() if k!='resultado_json'},'verification':check})
            assert r.json()['volume_above_m3']==analysis['resultado']['stats']['volume_above_m3']
            capture('volume_cota_'+str(reference));print('Volume #'+str(analysis['id'])+' '+json.dumps(check),flush=True)
            if reference==241:page.locator('.layer-control-item').filter(has_text=analysis['nome']).get_by_title('Remover camada',exact=True).click()
        first,last=[item['analysis'] for item in result['analyses']]
        assert last['resultado']['stats']['volume_above_m3']<first['resultado']['stats']['volume_above_m3']
        assert last['resultado']['stats']['volume_below_m3']>first['resultado']['stats']['volume_below_m3']
        slider=page.locator('.layer-control-item').filter(has_text=last['nome']).locator('input[type=range]')
        slider.focus();slider.press('Home')
        for _ in range(7):slider.press('ArrowRight')
        assert slider.input_value()=='0.35'
        page.wait_for_function("id=>[...document.querySelectorAll('.leaflet-tile-pane img')].filter(i=>i.src.includes('/analises/'+id+'/tile/')).every(i=>Math.abs(Number(getComputedStyle(i.closest('.leaflet-layer')).opacity)-.35)<.001)",arg=last['id'])
        result['opacity']=.35;capture('04_opacidade_35')
        page.reload(wait_until='networkidle')
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        aid=last['id'];row=page.locator(f'.result-item[data-analysis-id="{aid}"]');row.click();wait_tiles(aid)
        assert not page.locator('.leaflet-tile-pane img[src*="/api/ortomapas/"]').count()
        page.locator('.stats-panel').scroll_into_view_if_needed();capture('05_reabertura')
        with page.expect_download() as download:row.get_by_title('Baixar resultado GeoTIFF',exact=True).click()
        file=Path('/tmp')/f'volume_aoi_{aid}.tif';download.value.save_as(str(file))
        def digest(path):
            with open(path,'rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
        assert digest(file)==digest(last['resultado_path'])
        result['download']={'bytes':file.stat().st_size,'sha256':digest(file)}
        page.locator('.tools-panel').get_by_text('Vol',exact=True).click()
        page.locator('.tools-panel input[type=number]:visible').fill('242')
        page.locator('.terrain-aoi input:visible').check()
        expect(page.get_by_role('button',name='Calcular Volume',exact=True)).to_be_enabled()
        page.get_by_title('Limpar area de volume',exact=True).click()
        assert page.get_by_role('button',name='Calcular Volume',exact=True).is_disabled()
        assert not page.locator('.volume-result').count()
        result['clear_blocks_generation']=True;page.locator('.tools-panel .tool-form:visible').scroll_into_view_if_needed();capture('06_area_limpa')
        browser.close()
    outsider=login('fase1-outsider@example.test','validacao-fase1-outsider')
    result['outsider_result_status']=outsider.get(API+f'/analises/{aid}/resultado',timeout=30).status_code
    assert result['outsider_result_status']==403
    body={'dsm_path':'ortomapas/odm_2_dsm.tif','reference_elevation':241,'ortomapa_id':34,'projeto_id':62,
          'aoi':{'type':'Polygon','coordinates':[[[-38.05,-12.65],[-38.049,-12.65],[-38.049,-12.649],[-38.05,-12.65]]]}}
    result['outside_aoi_status']=session.post(API+'/tools/volume',json=body,timeout=30).status_code
    assert result['outside_aoi_status']==422
    project=session.get(API+'/projetos/2',timeout=30);project.raise_for_status()
    assert project.json()['pode_editar'] is False
    sources=session.get(API+'/ortomapas',params={'projeto_id':2},timeout=30);sources.raise_for_status()
    source=next(o for o in sources.json()['ortomapas'] if o['tipo']=='dsm')
    result['viewer_source_id']=source['id']
    result['viewer_publish_status']=session.post(API+'/tools/volume',json={'dsm_path':source['caminho_arquivo'],
        'reference_elevation':241,'ortomapa_id':source['id'],'projeto_id':2},timeout=30).status_code
    assert result['viewer_publish_status']==403
    assert not result['errors'];result['accepted']=True
    (OUT/'resultado.json').write_text(json.dumps(result,indent=2))
    print('Volume por AOI aceito; '+str(len(result['screens']))+' capturas',flush=True)


if __name__=='__main__':main()
