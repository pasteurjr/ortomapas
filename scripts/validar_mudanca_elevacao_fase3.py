"""Validate temporal elevation comparison with real DSMs and visual evidence."""
import hashlib
import io
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from playwright.sync_api import sync_playwright, expect
from rasterio.transform import from_bounds
from rasterio.warp import reproject, Resampling

from backend.database.connection import get_connection
from backend.utils.raster_tiles import tile_bounds
from backend.utils.resource_access import data_path
from scripts.validar_publicacao_terreno_fase3 import API, PROJECT, login

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/validacao/mudanca_elevacao_fase3_2026-10-13'
BEFORE_NAME = 'Aukerman - DSM real para derivadas'
AFTER_NAME = 'Aukerman - DSM campanha posterior controlada'


def expected_rgba(values, valid, style):
    threshold = style['threshold']
    palette = np.array([[178, 24, 43], [247, 247, 247], [247, 247, 247], [33, 102, 172]])
    stops = [style['min'], -threshold, threshold, style['max']]
    data = np.nan_to_num(values)
    rgb = np.stack([np.interp(data, stops, palette[:, i]) for i in range(3)], axis=-1).astype('uint8')
    alpha = (valid & (np.abs(data) > threshold)).astype('uint8') * 255
    rgba = np.dstack((rgb, alpha)); rgba[~valid, :3] = 0
    return rgba


def verify_analysis(session, analysis, before, after):
    result = analysis['resultado']; stats = result['stats']; threshold = result['style']['threshold']
    with rasterio.open(data_path(before['caminho_arquivo'])) as first, rasterio.open(data_path(after['caminho_arquivo'])) as second, rasterio.open(data_path(analysis['resultado_path'])) as output:
        assert output.crs == first.crs and output.res == first.res
        a = np.full((output.height, output.width), np.nan, dtype='float32')
        b = np.full_like(a, np.nan)
        for source, target in ((first, a), (second, b)):
            reproject(rasterio.band(source, 1), target, src_transform=source.transform, src_crs=source.crs,
                      src_nodata=source.nodata, dst_transform=output.transform, dst_crs=output.crs,
                      dst_nodata=np.nan, resampling=Resampling.bilinear)
        actual = output.read(1, masked=True)
        output_valid = ~np.ma.getmaskarray(actual) & np.isfinite(actual.data)
        expected = b - a
        valid = np.isfinite(expected) & output_valid
        error = float(np.max(np.abs(actual.data[valid] - expected[valid])))
        assert error < 0.00005
        pixel_area = abs(first.transform.a * first.transform.e - first.transform.b * first.transform.d)
        cut = valid & (expected < -threshold); fill = valid & (expected > threshold)
        stable = valid & ~(cut | fill)
        metrics = {
            'cut_volume_m3': float(np.abs(expected[cut]).sum() * pixel_area),
            'fill_volume_m3': float(expected[fill].sum() * pixel_area),
            'net_volume_m3': float((expected[fill].sum() - np.abs(expected[cut]).sum()) * pixel_area),
            'cut_area_m2': float(cut.sum() * pixel_area), 'fill_area_m2': float(fill.sum() * pixel_area),
            'stable_area_m2': float(stable.sum() * pixel_area), 'valid_area_m2': float(valid.sum() * pixel_area),
            'changed_percent': float((cut | fill).sum() * 100 / valid.sum()),
        }
        for key, value in metrics.items():
            tolerance = 0.011 if key != 'changed_percent' else 0.00011
            assert abs(stats[key] - value) < tolerance, (key, stats[key], value)
        assert abs(stats['min'] + 1.2) < 0.0001
        assert abs(stats['max'] - 1.5) < 0.0001

        center = result['aoi']['geometry']['coordinates'][0]
        lon = sum(point[0] for point in center[:-1]) / (len(center) - 1)
        lat = sum(point[1] for point in center[:-1]) / (len(center) - 1)
        z = 18; n = 2 ** z
        x = int((lon + 180) / 360 * n)
        y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
        tile = np.full((256, 256), np.nan, dtype='float32')
        reproject(rasterio.band(output, 1), tile, src_transform=output.transform, src_crs=output.crs,
                  src_nodata=output.nodata, dst_transform=from_bounds(*tile_bounds(z, x, y), 256, 256),
                  dst_crs='EPSG:3857', dst_nodata=np.nan, resampling=Resampling.nearest)
    valid_tile = np.isfinite(tile)
    expected_tile = expected_rgba(tile, valid_tile, result['style'])
    response = session.get(API + f"/analises/{analysis['id']}/tile/{z}/{x}/{y}.png", timeout=60)
    response.raise_for_status(); obtained = np.asarray(Image.open(io.BytesIO(response.content)))
    assert np.array_equal(obtained, expected_tile)
    assert (obtained[..., 3] == 0).any() and (obtained[..., 3] == 255).any()
    Image.fromarray(obtained).save(OUT / f"tile_{analysis['id']}.png")
    return {**metrics, 'valid_pixels': int(valid.sum()), 'max_raster_error_m': error,
            'tile_rgba_exact': True, 'transparent_stable_pixels': int((obtained[..., 3] == 0).sum())}


def select_option(page, selector, label):
    selector.click(); page.get_by_role('option', name=label, exact=True).last.click()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    session = login('phase1-1791391595@example.test', 'fase1-senha-segura')
    catalog = session.get(API + '/ortomapas', params={'projeto_id': 62}, timeout=30).json()['ortomapas']
    before = next(item for item in catalog if item['nome'] == BEFORE_NAME)
    after = next(item for item in catalog if item['nome'] == AFTER_NAME)
    result = {'accepted': False, 'errors': [], 'screens': [], 'before_id': before['id'], 'after_id': after['id']}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1024}); page.set_default_timeout(60000)
        page.on('pageerror', lambda error: result['errors'].append(str(error)))
        page.goto('http://127.0.0.1:5302', wait_until='networkidle')
        page.locator('input[type=email]').fill('phase1-1791391595@example.test')
        page.locator('input[type=password]').fill('fase1-senha-segura')
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.locator('.project-selector').click(); page.get_by_role('option', name=PROJECT, exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='Aukerman - ortofoto ODM real').get_by_title('Visibilidade', exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises', exact=True).click()
        page.locator('.tools-panel').get_by_text('Mud', exact=True).click()
        selects = page.locator('.tools-panel .p-select:visible'); expect(selects).to_have_count(2)
        select_option(page, selects.nth(0), BEFORE_NAME + ' (dsm)')
        select_option(page, selects.nth(1), AFTER_NAME + ' (dsm)')
        button = page.get_by_role('button', name='Comparar Elevacoes', exact=True)
        expect(button).to_be_enabled()
        page.locator('.tools-panel .terrain-aoi input:visible').check(); expect(button).to_be_disabled()
        page.get_by_title('Desenhar area de comparacao', exact=True).click()
        page.locator('.leaflet-mouse-marker').wait_for(state='attached')
        bounds = page.locator('.leaflet-container').bounding_box(); cx = bounds['x'] + bounds['width'] / 2; cy = bounds['y'] + bounds['height'] / 2
        points = [(cx-145, cy-105), (cx+145, cy-105), (cx+145, cy+105), (cx-145, cy+105)]
        for number, point in enumerate(points):
            page.mouse.click(*point, delay=100); page.wait_for_timeout(100)
            page.wait_for_function('n=>document.querySelectorAll(".leaflet-editing-icon").length===n', arg=number+1)
        page.mouse.click(*points[0]); page.get_by_text('Area selecionada', exact=True).wait_for()

        def capture(name):
            page.evaluate('()=>document.fonts.ready')
            page.wait_for_function("()=>[...document.querySelectorAll('.leaflet-tile-pane img')].every(i=>i.complete&&i.naturalWidth>0&&getComputedStyle(i).opacity==='1')")
            page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
            page.screenshot(path=str(OUT / f'{name}.png'), full_page=False)
            result['screens'].append(f'{name}.png')

        capture('01_parametros_e_aoi')
        with page.expect_response(lambda response: response.url.endswith('/tools/volume/difference') and response.request.method == 'POST', timeout=180000) as event:
            button.click()
        response = event.value; assert response.status == 200, response.text()
        payload = response.json(); analysis = payload['analise']; result['analysis_id'] = analysis['id']; result['comparison_id'] = payload['comparacao_id']
        assert analysis['tipo_analise'] == 'mudancas' and analysis['ortomapa_id'] == after['id']
        page.wait_for_function("id=>[...document.querySelectorAll('.leaflet-tile-pane img')].some(i=>i.src.includes('/analises/'+id+'/tile/')&&i.complete&&i.naturalWidth===256)", arg=analysis['id'])
        page.locator('.change-result').scroll_into_view_if_needed(); capture('02_resultado_mudanca')
        verification = verify_analysis(session, analysis, before, after); result['verification'] = verification
        legend = page.locator('.map-legend, .layer-legend').filter(has_text='Deposicao').first
        if legend.count(): legend.scroll_into_view_if_needed()
        capture('03_mapa_remocao_deposicao')

        page.reload(wait_until='networkidle')
        page.locator('.project-selector').click(); page.get_by_role('option', name=PROJECT, exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='Aukerman - ortofoto ODM real').get_by_title('Visibilidade', exact=True).click()
        page.locator('.workspace-sidebar-nav').get_by_text('Análises', exact=True).click()
        row = page.locator(f'.result-item[data-analysis-id="{analysis["id"]}"]'); row.click()
        page.wait_for_function("id=>[...document.querySelectorAll('.leaflet-tile-pane img')].some(i=>i.src.includes('/analises/'+id+'/tile/')&&i.complete)", arg=analysis['id'])
        page.locator('.stats-panel').scroll_into_view_if_needed(); capture('04_persistencia_e_estatisticas')
        with page.expect_download() as download:
            row.get_by_title('Baixar resultado GeoTIFF', exact=True).click()
        downloaded = Path('/tmp') / f'mudanca_elevacao_{analysis["id"]}.tif'; download.value.save_as(str(downloaded))
        digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        assert digest(downloaded) == digest(data_path(analysis['resultado_path']))
        result['download'] = {'bytes': downloaded.stat().st_size, 'sha256': digest(downloaded)}
        browser.close()

    body = {'ortomapa_antes_id': after['id'], 'ortomapa_depois_id': before['id'], 'projeto_id': 62,
            'dsm1_path': after['caminho_arquivo'], 'dsm2_path': before['caminho_arquivo'],
            'threshold': 0.1, 'aoi': analysis['resultado']['aoi']['geometry'], 'output_name': 'mudanca_invertida_validacao'}
    reverse = session.post(API + '/tools/volume/difference', json=body, timeout=180); reverse.raise_for_status(); reverse = reverse.json()
    assert reverse['cut_volume_m3'] == payload['fill_volume_m3']
    assert reverse['fill_volume_m3'] == payload['cut_volume_m3']
    assert reverse['net_volume_m3'] == -payload['net_volume_m3']
    result['reverse'] = {key: reverse[key] for key in ('cut_volume_m3', 'fill_volume_m3', 'net_volume_m3')}

    same = {**body, 'ortomapa_antes_id': before['id'], 'ortomapa_depois_id': before['id'],
            'dsm1_path': before['caminho_arquivo'], 'dsm2_path': before['caminho_arquivo']}
    result['same_model_status'] = session.post(API + '/tools/volume/difference', json=same, timeout=30).status_code
    assert result['same_model_status'] == 422
    outsider = login('fase1-outsider@example.test', 'validacao-fase1-outsider')
    result['outsider_status'] = outsider.post(API + '/tools/volume/difference', json=body, timeout=30).status_code
    assert result['outsider_status'] == 403
    with get_connection() as connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute('SELECT * FROM comparacoes_temporais WHERE id=%s', (result['comparison_id'],))
        comparison = cursor.fetchone()
    assert comparison and comparison['ortomapa_antes_id'] == before['id'] and comparison['ortomapa_depois_id'] == after['id']
    result['database_record'] = {'id': comparison['id'], 'tipo': comparison['tipo_comparacao'],
                                 'antes': comparison['ortomapa_antes_id'], 'depois': comparison['ortomapa_depois_id']}
    assert not result['errors']; result['accepted'] = True
    (OUT / 'resultado.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    main()
