"""Exercise real terrain UI, HTTP and raster outputs; never create empty layers."""
import json
from pathlib import Path

import numpy as np
import rasterio
import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/validacao/derivadas_terreno_fase2_2026-10-11'
API = 'http://127.0.0.1:5018/api'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {'accepted': False, 'errors': [], 'operations': [], 'screens': []}
    target = OUT/'resultado.json'
    target.write_text(json.dumps(result))
    session = requests.Session()
    login = session.post(API+'/auth/login', json={'email':'phase1-1791391595@example.test','senha':'fase1-senha-segura'}, timeout=30)
    login.raise_for_status()
    session.headers['Authorization'] = 'Bearer '+login.json()['access_token']
    source = ROOT/'data/ortomapas/odm_2_dsm.tif'
    denied = session.post(API+'/tools/aspect',json={'input_path':str(source),'projeto_id':2,'output_name':'visualizador_recusado'},timeout=30)
    assert denied.status_code == 403
    result['viewer_write_status'] = denied.status_code
    project_name = 'Validacao Fase 1 - Ortofoto real Aukerman'
    projects = session.get(API+'/projetos');projects.raise_for_status()
    project = next(p for p in projects.json()['projetos'] if p['nome']==project_name)
    response = session.get(API+'/ortomapas',params={'projeto_id':project['id']});response.raise_for_status()
    orthos = response.json()['ortomapas']
    ortho = next(o for o in orthos if o['nome']=='Aukerman - ortofoto ODM real')
    dsm = next((o for o in orthos if o['nome']=='Aukerman - DSM real para derivadas'),None)
    if dsm is None:
        from rasterio.warp import transform_bounds
        with rasterio.open(source) as src:
            west,south,east,north = transform_bounds(src.crs,4326,*src.bounds)
            created = session.post(API+'/ortomapas',json={'projeto_id':project['id'],'voo_id':ortho['voo_id'],
                'nome':'Aukerman - DSM real para derivadas','tipo':'dsm','caminho_arquivo':str(source.relative_to(ROOT/'data')),
                'status':'disponivel','sistema_coordenadas':str(src.crs),'largura_px':src.width,'altura_px':src.height,
                'bbox_oeste':west,'bbox_sul':south,'bbox_leste':east,'bbox_norte':north,'resolucao_cm':abs(src.res[0])*100})
            created.raise_for_status();dsm=created.json()
    result['project_id']=project['id'];result['dsm_id']=dsm['id']
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width':1440, 'height':900})
        page.set_default_timeout(30000)
        page.on('pageerror', lambda e: result['errors'].append(str(e)))
        page.goto('http://127.0.0.1:5302', wait_until='networkidle')
        page.locator('input[type=email]').fill('phase1-1791391595@example.test')
        page.locator('input[type=password]').fill('fase1-senha-segura')
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.locator('.project-selector').click()
        page.get_by_role('option', name=project_name, exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='Aukerman - ortofoto ODM real').get_by_title('Visibilidade',exact=True).click()
        page.wait_for_function("""() => { const tiles=[...document.querySelectorAll('.leaflet-tile-pane img')].filter(i=>i.src.includes('/api/ortomapas/')); return tiles.length>0 && tiles.every(i=>i.complete && i.naturalWidth===256 && getComputedStyle(i).opacity==='1') }""")
        page.locator('.workspace-sidebar-nav').get_by_text('Análises', exact=True).click()
        print('Menu analises aberto',flush=True)
        page.screenshot(path=str(OUT/'diagnostico_menu.png'))
        page.locator('.tools-panel').get_by_text('Ter',exact=True).click()
        print('Terreno aberto',flush=True)
        page.screenshot(path=str(OUT/'diagnostico_terreno.png'))
        layers_before = page.locator('.layer-item').count()
        for operation,label in [('aspect','Aspecto (Aspect)'),('hillshade','Sombreamento (Hillshade)')]:
            page.locator('.tools-panel .p-select:visible').nth(1).click()
            page.get_by_role('option', name=label,exact=True).click()
            print('Operacao selecionada: '+operation,flush=True)
            with page.expect_response(lambda r: r.url.endswith('/tools/'+operation) and r.request.method=='POST') as response:
                page.get_by_role('button',name='Gerar Analise',exact=True).click()
            r = response.value
            assert r.status == 200, r.text()
            data = r.json()
            input_path = r.request.post_data_json['input_path']
            with rasterio.open(ROOT/'data'/input_path if not Path(input_path).is_absolute() else input_path) as src:
                values = src.read(1,masked=True).astype(float).filled(np.nan)
                assert src.crs.to_epsg() == 32617 and src.transform.b == 0 and src.transform.d == 0
                # Independent physical gradients for this north-up metre dataset.
                north,east = np.gradient(values,src.transform.e,src.transform.a)
                valid = np.isfinite(values)&np.isfinite(east)&np.isfinite(north)
                if operation=='aspect':
                    expected = np.mod(np.degrees(np.arctan2(-east,-north)),360)
                    valid &= np.hypot(east,north)>1e-12
                else:
                    light = np.array([np.sin(np.radians(315))*np.cos(np.radians(45)),np.cos(np.radians(315))*np.cos(np.radians(45)),np.sin(np.radians(45))])
                    expected = np.clip((-east*light[0]-north*light[1]+light[2])/np.sqrt(1+east**2+north**2),0,1)*255
            with rasterio.open(data['output_path']) as src:
                actual = src.read(1,masked=True)
                assert np.array_equal(~np.ma.getmaskarray(actual),valid)
                assert np.allclose(actual.data[valid],expected[valid],atol=2e-5)
            page.locator('.terrain-result').wait_for()
            displayed=page.locator('.terrain-result').inner_text()
            for key in ('min','max','mean'):
                assert f"{data['statistics']['band_1'][key]:.2f}" in displayed
            assert not page.locator('.tools-panel [role=alert]').count()
            assert page.locator('.layer-item').count()==layers_before
            page.evaluate('()=>document.fonts.ready')
            name=operation+'.png';page.screenshot(path=str(OUT/name));result['screens'].append(name)
            result['operations'].append({'operation':operation,'input_path':input_path,'result':data,'verified_pixels':int(valid.sum())})
        browser.close()
    path=str(source)
    response=session.post(API+'/tools/volume/difference',json={'dsm1_path':path,'dsm2_path':path,'output_name':'regressao_terreno_identidade'},timeout=120)
    response.raise_for_status();identity=response.json()
    assert identity['cut_volume_m3']==0 and identity['fill_volume_m3']==0 and identity['max_diff_m']==0
    result['identity_difference']=identity
    response=session.post(API+'/tools/hillshade',json={'input_path':path,'output_name':'invalido','altitude':100},timeout=30)
    assert response.status_code==422
    result['invalid_altitude_status']=response.status_code
    assert not result['errors']
    result['accepted']=True
    target.write_text(json.dumps(result,indent=2))
    print(json.dumps({'accepted':result['accepted'],'errors':result['errors'],'screens':result['screens'],
        'operations':[{'operation':o['operation'],'verified_pixels':o['verified_pixels']} for o in result['operations']]},indent=2))


if __name__=='__main__': main()
