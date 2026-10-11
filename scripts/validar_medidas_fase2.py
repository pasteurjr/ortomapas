"""Actual HTTP metric outputs and real LAZ pointer measurement, with screenshots."""
import base64
import io
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
import requests
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT / 'docs/validacao/medidas_fase2_2026-10-10'
API = 'http://127.0.0.1:5018/api'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {'accepted': False, 'http': [], 'screens': [], 'browser_errors': []}
    output = OUT / 'resultado.json'
    output.write_text(json.dumps(result))
    session = requests.Session()
    login = session.post(API+'/auth/login', json={'email':'phase1-1791391595@example.test','senha':'fase1-senha-segura'}, timeout=30)
    login.raise_for_status()
    session.headers['Authorization'] = 'Bearer '+login.json()['access_token']

    def tool(name, args):
        response = session.post(API+'/agents/tools/execute', json={'name':name,'arguments':args}, timeout=120)
        response.raise_for_status()
        data = response.json()['dados']
        result['http'].append({'tool':name,'input':args,'output':data})
        return data
    rectangle = {'type':'Polygon','coordinates':[[[500000,8600000],[500100,8600000],[500100,8600200],[500000,8600200],[500000,8600000]]]}
    metric = tool('medir_geometria', {'geometry':rectangle,'crs':'EPSG:32724'})
    assert metric['area_m2'] == 20000 and metric['perimetro_m'] == 600
    point = {'type':'Point','coordinates':[-38.046,-12.654]}
    buffer = tool('buffer_geometria', {'geometry':point,'distancia':100})
    metric = tool('medir_geometria', {'geometry':buffer['geometry']})
    assert abs(metric['area_m2']-np.pi*100**2)/(np.pi*100**2) < .002
    distance = tool('distancia_geometrias', {'a':{'type':'Point','coordinates':[0,0]},'b':{'type':'Point','coordinates':[3,4]},'crs':'EPSG:32724'})
    assert distance['distancia_m'] == 5
    slope = tool('calcular_declividade', {'produto_id':5})
    with rasterio.open(ROOT/'data/ortomapas/odm_2_dsm.tif') as ds:
        shape = tuple(slope['grade'])
        sampled = ds.read(1,out_shape=shape,masked=True,resampling=rasterio.enums.Resampling.bilinear).astype(float).filled(np.nan)
        gy,gx = np.gradient(sampled, abs(ds.transform.e)*ds.height/shape[0], abs(ds.transform.a)*ds.width/shape[1])
        degrees = np.degrees(np.arctan(np.hypot(gx,gy)))
        valid = np.isfinite(sampled) & np.isfinite(degrees)
        expected_slope = float(degrees[valid].mean())
        arr = ds.read(1,masked=True).astype(float).filled(np.nan)
        elevations = arr[np.isfinite(arr)]
        area = abs(ds.transform.a*ds.transform.e-ds.transform.b*ds.transform.d)
        cota = 240.
        expected_volume = float(np.maximum(elevations-cota,0).sum()*area)
    assert abs(slope['media']-expected_slope) < 1e-9
    volume = tool('calcular_volume', {'produto_id':5,'cota':cota})
    assert abs(volume['volume_acima_m3']-expected_volume) < 1e-6
    result['reference'] = {'slope_mean_expected':expected_slope,'volume_expected_m3':expected_volume,'vertical_assumption':'raster Z in metres, datum not field-verified'}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width':1440,'height':900})
        page.set_default_timeout(30000)
        page.on('pageerror', lambda e: result['browser_errors'].append(str(e)))
        cloud = []
        def response(r):
            if '/points?' in r.url and r.status == 200:
                cloud.append(r.json())
        page.on('response', response)
        page.goto('http://127.0.0.1:5302', wait_until='networkidle')
        page.locator('input[type=email]').fill('phase1-1791391595@example.test')
        page.locator('input[type=password]').fill('fase1-senha-segura')
        page.get_by_role('button',name='Entrar',exact=True).click()
        page.evaluate("localStorage.setItem('ortomapas.viewer3d.settings', JSON.stringify({sampleLimit:60000}))")
        page.locator('.project-selector').click()
        page.get_by_role('option',name='Teste PostgreSQL UI',exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Voos e ODM',exact=True).click()
        page.locator('.task-row').filter(has_text='f7563d3d').get_by_role('button',name='Abrir 3D',exact=True).click()
        page.get_by_text('Carregando amostra...',exact=True).wait_for(state='detached')
        assert not page.locator('.viewer-shell .overlay.error').count()
        assert cloud and cloud[-1]['sampled'] > 1000
        canvas = page.locator('.viewer-shell canvas')
        def settle():
            page.evaluate('() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))')
        def capture(name):
            settle()
            page.screenshot(path=str(OUT/(name+'.png')))
            result['screens'].append(name+'.png')
        raw = canvas.evaluate("c=>c.toDataURL('image/png').split(',')[1]")
        pixels = np.asarray(Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGB'))
        coverage = float(np.any(np.abs(pixels.astype(int)-[16,24,32])>10,axis=2).mean())
        assert coverage > .02
        result['canvas_coverage'] = coverage
        capture('01_nuvem_real')
        print('Nuvem renderizada', flush=True)
        page.get_by_title('Vista superior',exact=True).click(); settle()
        print('Vista superior', flush=True)
        page.get_by_role('button',name='Inspecionar ponto',exact=True).click()
        print('Inspecao ativada', flush=True)
        box = canvas.bounding_box()
        choices = []
        for fy in (.35,.45,.55,.65):
            for fx in (.3,.4,.5,.6,.7):
                x,y = box['x']+box['width']*fx,box['y']+box['height']*fy
                page.mouse.click(x,y); settle()
                values = page.locator('.point-result b').all_text_contents()
                if values:
                    xyz = [float(v.replace(' m','')) for v in values[:3]]
                    if not choices or np.linalg.norm(np.array(xyz)-choices[0]['xyz']) > 10:
                        choices.append({'screen':[x,y],'xyz':xyz})
                if len(choices) == 2: break
            if len(choices) == 2: break
        assert len(choices) == 2, 'Could not inspect two separated real points with actual pointer clicks'
        capture('02_inspecao_coordenadas')
        page.get_by_role('button',name='Medir distância',exact=True).click()
        for choice in choices:
            page.mouse.click(*choice['screen']); settle()
        displayed = page.locator('.measure-result b').inner_text()
        measured = float(displayed.replace(' m',''))
        endpoints = [[float(v) for v in text.replace(' m','').split(' / ')] for text in page.locator('.endpoint-result span').all_text_contents()]
        assert len(endpoints) == 2
        expected = float(np.linalg.norm(np.array(endpoints[0])-endpoints[1]))
        assert abs(measured-expected) < .03
        coords = np.column_stack([cloud[-1]['points'][axis] for axis in ('x','y','z')])
        assert all(np.min(np.linalg.norm(coords-endpoint,axis=1)) < .02 for endpoint in endpoints)
        result['measurement'] = {'source':'real LAZ API sample','endpoints_rounded_m':endpoints,'expected_from_displayed_endpoints_m':expected,'displayed_m':measured,'tolerance_m':.03}
        capture('03_medicao_metros')
        page.get_by_label('Exagero vertical da nuvem',exact=True).fill('3')
        assert page.locator('.measure-result b').inner_text() == displayed
        assert page.locator('.endpoint-result span').all_text_contents() == [ ' / '.join(f'{v:.2f}' for v in endpoint)+' m' for endpoint in endpoints ]
        capture('06_exagero_3x_medida_preservada')
        with page.expect_download() as download:
            page.get_by_title('Exportar imagem PNG',exact=True).click()
        download.value.save_as('/tmp/nuvem_fase2_exportada.png')
        assert Image.open('/tmp/nuvem_fase2_exportada.png').size[0] > 500
        with page.expect_download() as download:
            page.get_by_title('Exportar pontos CSV',exact=True).click()
        download.value.save_as('/tmp/nuvem_fase2_exportada.csv')
        lines = Path('/tmp/nuvem_fase2_exportada.csv').read_text().splitlines()
        assert len(lines)-1 == cloud[-1]['sampled']
        result['exports'] = {'png':True,'csv_rows':len(lines)-1}
        lo, hi = cloud[-1]['bounds']['min'][2], cloud[-1]['bounds']['max'][2]
        threshold = round(lo + int((hi-lo)/.2)*.1, 2)
        page.locator('.viewer-shell input[type=range]').nth(3).fill(str(threshold))
        assert page.locator('.measure-result').count() == 0
        assert page.locator('.point-result').count() == 0
        stats = page.locator('.stats b').all_text_contents()
        assert int(stats[1].replace('.','')) < cloud[-1]['sampled']
        result['filtered_visible_points'] = int(stats[1].replace('.',''))
        capture('04_recorte_limpa_medicao')
        page.set_viewport_size({'width':1024,'height':768}); settle()
        canvas_box=canvas.bounding_box(); panel=page.locator('.tools-panel').bounding_box()
        assert canvas_box['x']+canvas_box['width'] <= panel['x']+1
        capture('05_tablet_sem_sobreposicao')
        assert not result['browser_errors'], result['browser_errors']
        browser.close()
    result['accepted'] = True
    output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'http'},indent=2))


if __name__ == '__main__':
    main()
