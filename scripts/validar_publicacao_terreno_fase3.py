"""End-to-end real terrain publication, persistence, downloads and scoped tiles."""
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
import requests
import rasterio
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/validacao/publicacao_terreno_fase3_2026-10-11'
API='http://127.0.0.1:5018/api'
PROJECT='Validacao Fase 1 - Ortofoto real Aukerman'


def login(email,password):
    session=requests.Session()
    response=session.post(API+'/auth/login',json={'email':email,'senha':password},timeout=30)
    response.raise_for_status()
    session.headers['Authorization']='Bearer '+response.json()['access_token']
    return session


def verify_tile(session,analysis):
    result=analysis['resultado'];kind=result['style']['kind'];z=17
    lon=result['bbox_oeste'];lat=(result['bbox_sul']+result['bbox_norte'])/2
    x=int((lon+180)/360*2**z);y=int((1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*2**z)
    span=40075016.68557849/2**z;left=-20037508.342789244+x*span;top=20037508.342789244-y*span
    tile=session.get(API+f"/analises/{analysis['id']}/tile/{z}/{x}/{y}.png",timeout=60)
    tile.raise_for_status();actual=np.asarray(Image.open(io.BytesIO(tile.content)))
    with rasterio.open(analysis['resultado_path']) as ds:
        grid=np.full((256,256),-9999,dtype='float32')
        reproject(rasterio.band(ds,1),grid,src_transform=ds.transform,src_crs=ds.crs,src_nodata=-9999,
                  dst_transform=from_bounds(left,top-span,left+span,top,256,256),dst_crs='EPSG:3857',dst_nodata=-9999,
                  resampling=Resampling.nearest if kind=='aspect' else Resampling.bilinear)
    valid=(grid!=-9999)&np.isfinite(grid)
    safe=np.where(valid,grid,0)
    if kind=='aspect':
        colors=np.array([[220,69,69],[223,132,53],[215,198,52],[76,170,102],[48,170,168],[64,133,209],[115,82,185],[190,88,159]])
        rgb=colors[(np.floor((safe+22.5)/45).astype(int)%8)]
    elif kind=='hillshade': rgb=np.repeat(np.clip(safe,0,255).astype('uint8')[...,None],3,axis=2)
    else:
        colors=np.array([[38,118,74],[215,198,52],[223,132,53],[220,69,69],[115,82,185]])
        rgb=np.stack([np.interp(safe,[0,10,30,60,90],colors[:,i]) for i in range(3)],axis=2).astype('uint8')
    expected=np.dstack([rgb,valid.astype('uint8')*255]).astype('uint8');expected[~valid,:3]=0
    difference=np.abs(actual.astype(float)-expected)
    exact=float(np.mean(np.all(actual==expected,axis=2)))
    alpha=float(np.mean(actual[:,:,3]==expected[:,:,3]));error=float(difference.mean())
    assert 0<np.count_nonzero(actual[:,:,3])<256*256
    assert exact>=.97 and alpha>=.995 and error<1.5,(kind,exact,alpha,error)
    Image.fromarray(expected).save(OUT/f'{kind}_tile_esperado.png')
    Image.fromarray(actual).save(OUT/f'{kind}_tile_obtido.png')
    return {'z':z,'x':x,'y':y,'exact_fraction':exact,'alpha_match':alpha,'mean_channel_error':error,
            'opaque_pixels':int(np.count_nonzero(actual[:,:,3]))}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    result={'accepted':False,'errors':[],'screens':[],'analyses':[],'checks':[],'download_responses':[]}
    target=OUT/'resultado.json';target.write_text(json.dumps(result))
    session=login('phase1-1791391595@example.test','fase1-senha-segura')
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(viewport={'width':1440,'height':900});page.set_default_timeout(60000)
        page.on('pageerror',lambda e:result['errors'].append(str(e)))
        page.on('response',lambda r:result['download_responses'].append({'path':r.url.split('?')[0].split('/api')[-1],'status':r.status}) if '/download-access' in r.url or '/resultado?' in r.url else None)
        page.goto('http://127.0.0.1:5302',wait_until='networkidle')
        page.locator('input[type=email]').fill('phase1-1791391595@example.test')
        page.locator('input[type=password]').fill('fase1-senha-segura')
        page.get_by_role('button',name='Entrar',exact=True).click()
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='Aukerman - ortofoto ODM real').get_by_title('Visibilidade',exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        page.locator('.tools-panel').get_by_text('Ter',exact=True).click()
        def capture(name):
            page.evaluate('()=>document.fonts.ready')
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            rect=page.locator('.toolbar').bounding_box();assert rect['y']==0 and rect['height']==48
            bounds=page.locator('.sidebar-left .sidebar-content').evaluate('(el)=>[...el.children].map(e=>e.getBoundingClientRect().toJSON())')
            assert all(a['bottom']<=b['top'] for a,b in zip(bounds,bounds[1:])),bounds
            page.screenshot(path=str(OUT/(name+'.png')));result['screens'].append(name+'.png')
        def wait_tiles(aid):
            page.wait_for_function("""id=>{ const t=[...document.querySelectorAll('.leaflet-tile-pane img')].filter(i=>i.src.includes('/api/analises/'+id+'/tile/'));return t.length>0&&t.every(i=>i.complete&&i.naturalWidth===256&&getComputedStyle(i).opacity==='1') }""",arg=aid)
        for kind,label in [('aspect','Aspecto (Aspect)'),('hillshade','Sombreamento (Hillshade)'),('slope','Declividade (Slope)')]:
            page.locator('.tools-panel .p-select:visible').nth(1).click();page.get_by_role('option',name=label,exact=True).click()
            with page.expect_response(lambda r:r.url.endswith('/tools/'+kind) and r.request.method=='POST') as response:
                page.get_by_role('button',name='Gerar Analise',exact=True).click()
            r=response.value;assert r.status==200,r.text()
            analysis=r.json()['analise'];aid=analysis['id'];assert analysis['projeto_id']==62 and analysis['ortomapa_id']==34
            assert analysis['resultado']['provenance']['operation']==kind
            print('Publicado: '+kind+' #'+str(aid),flush=True)
            wait_tiles(aid)
            assert page.locator(f'.raster-legend[data-analysis-id="{aid}"]').count()==1
            item=page.locator('.layer-control-item').filter(has_text=analysis['nome'])
            assert item.count()==1
            page.locator('.tools-panel .section-title').scroll_into_view_if_needed()
            page.locator('.tools-panel .tool-form:visible').scroll_into_view_if_needed()
            capture(kind+'_publicado')
            verification=verify_tile(session,analysis)
            result['analyses'].append({'analysis':analysis,'tile_verification':verification})
            item.get_by_title('Remover camada',exact=True).click()
        last=result['analyses'][-1]['analysis'];aid=last['id']
        page.reload(wait_until='networkidle')
        page.locator('.project-selector').click();page.get_by_role('option',name=PROJECT,exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises',exact=True).click()
        page.locator('.tools-panel').get_by_text('Ter',exact=True).click()
        row=page.locator(f'.result-item[data-analysis-id="{aid}"]')
        row.click()
        page.screenshot(path=str(OUT/'diagnostico_reabertura.png'))
        print('Reabertura do registro #'+str(aid),flush=True)
        wait_tiles(aid)
        capture('resultado_reaberto_sem_origem')
        assert not page.locator('.leaflet-tile-pane img[src*="/api/ortomapas/"]').count()
        assert page.locator('.stats-panel').count()==1
        control=page.locator('.layer-control-item').filter(has_text='Declividade')
        control.locator('input[type=range]').fill('0.35')
        page.wait_for_function("""id=>[...document.querySelectorAll('.leaflet-layer')].some(l=>l.querySelector('img[src*="/api/analises/'+id+'/tile/"]')&&Math.abs(parseFloat(l.style.opacity)-.35)<.001)""",arg=aid)
        capture('opacidade_35_porcento')
        control.locator('input[type=range]').fill('1')
        print('Iniciando download #'+str(aid),flush=True)
        try:
            with page.expect_download(timeout=30000) as download:
                row.get_by_title('Baixar resultado GeoTIFF',exact=True).click()
        except Exception:
            page.screenshot(path=str(OUT/'diagnostico_download.png'))
            print('Download responses: '+json.dumps(result['download_responses']),flush=True)
            print('Alert: '+str(page.locator('.result-error').all_text_contents()),flush=True)
            raise
        destination=Path('/tmp')/f'analise_{aid}.tif';download.value.save_as(str(destination))
        def sha(path):
            with open(path,'rb') as file:return hashlib.file_digest(file,'sha256').hexdigest()
        assert sha(destination)==sha(last['resultado_path'])
        result['download']={'id':aid,'bytes':destination.stat().st_size,'sha256':sha(destination)}
        page.locator('.stats-panel').scroll_into_view_if_needed()
        capture('catalogo_download_e_proveniencia')
        browser.close()
    outsider=login('fase1-outsider@example.test','validacao-fase1-outsider')
    def check(name,response,expected):
        result['checks'].append({'name':name,'expected':expected,'actual':response.status_code})
        assert response.status_code==expected,(name,response.text[:250])
    check('catalogo anonimo',requests.get(API+'/analises',timeout=30),401)
    check('projeto alheio',outsider.get(API+'/analises',params={'projeto_id':62},timeout=30),403)
    for path in [f'/analises/{aid}',f'/analises/{aid}/resultado',f'/analises/{aid}/download-access',f'/analises/{aid}/tile-access',f'/analises/{aid}/tile/17/35770/48995.png']:
        check('acesso alheio '+path,outsider.get(API+path,timeout=30),403)
    all_rows=outsider.get(API+'/analises',timeout=30);all_rows.raise_for_status()
    assert not any(row['projeto_id']==62 for row in all_rows.json()['analises'])
    access=session.get(API+f'/analises/{aid}/tile-access',timeout=30);access.raise_for_status()
    url=access.json()['url'].replace('{z}','17').replace('{x}','35770').replace('{y}','48995')
    check('ticket restrito valido',requests.get('http://127.0.0.1:5018'+url,timeout=60),200)
    other=result['analyses'][0]['analysis']['id']
    check('ticket nao vale para outra analise',requests.get('http://127.0.0.1:5018'+url.replace(f'/{aid}/tile/',f'/{other}/tile/'),timeout=30),401)
    access=session.get(API+f'/analises/{aid}/download-access',timeout=30);access.raise_for_status()
    wrong=access.json()['url'].replace(f'/{aid}/resultado',f'/{other}/resultado')
    check('ticket download nao vale para outra analise',requests.get('http://127.0.0.1:5018'+wrong,timeout=30),401)
    check('XYZ invalido',session.get(API+f'/analises/{aid}/tile/23/0/0.png',timeout=30),422)
    mismatch=session.post(API+'/tools/aspect',json={'input_path':'ortomapas/odm_2_dsm.tif','output_name':'mismatch','ortomapa_id':30,'projeto_id':62},timeout=30)
    check('origem RGB recusada',mismatch,422)
    assert not result['errors']
    result['accepted']=True;target.write_text(json.dumps(result,indent=2))
    print(json.dumps({'accepted':True,'screens':result['screens'],'checks':result['checks'],'tiles':[a['tile_verification'] for a in result['analyses']]},indent=2))


if __name__=='__main__':main()
