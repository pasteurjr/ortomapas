"""Visual proof of crop and GeoTIFF export using an existing real orthophoto."""

import os
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'docs/validacao/recorte_exportacao_fase5_2026-10-15'
OUT.mkdir(parents=True, exist_ok=True)


def wait_for_tiles(page, endpoint):
    page.wait_for_function("""endpoint => {
      const tiles = [...document.querySelectorAll('img.leaflet-tile')]
        .filter(tile => tile.src.includes(endpoint))
      return tiles.length > 0 && tiles.every(tile => tile.complete && tile.naturalWidth === 256)
    }""", arg=endpoint, timeout=30000)
    page.wait_for_timeout(500)


def test_crop_and_export():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(15000)
        page.goto(os.getenv('FRONTEND_URL', 'http://127.0.0.1:5176'), wait_until='networkidle')
        page.locator('input[type=email]').fill(os.getenv('E2E_EMAIL', 'phase1-1791391595@example.test'))
        page.locator('input[type=password]').fill(os.getenv('E2E_PASSWORD', 'fase1-senha-segura'))
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.get_by_text('Validacao Fase 1 - Ortofoto real Aukerman', exact=True).first.click()
        card = page.locator('.ortomapa-card').filter(has_text='Aukerman - ortofoto ODM real')
        card.wait_for()
        card.get_by_title('Visibilidade').click()
        wait_for_tiles(page, '/api/ortomapas/30/tile/')
        page.locator('.workspace-sidebar-nav').get_by_text('Análises', exact=True).click()
        page.get_by_text('Rec', exact=True).click()
        page.screenshot(path=str(OUT / '01_recorte_entrada.png'))
        page.get_by_role('button', name='Desenhar Poligono de Recorte').click()
        page.locator('.leaflet-container').wait_for()
        bounds = page.locator('.leaflet-container').bounding_box()
        assert bounds
        points = [(0.42, 0.38), (0.58, 0.38), (0.50, 0.58)]
        for rx, ry in points:
            page.mouse.click(bounds['x'] + bounds['width'] * rx, bounds['y'] + bounds['height'] * ry)
            page.wait_for_timeout(350)
        page.get_by_role('button', name='Concluir poligono').click()
        page.get_by_text('Area selecionada', exact=True).wait_for()
        page.screenshot(path=str(OUT / '02_aoi_desenhada.png'))
        with page.expect_response(lambda response: response.request.method == 'POST' and response.url.endswith('/tools/recorte')) as crop_response:
            page.get_by_role('button', name='Recortar', exact=True).click()
        page.get_by_text('Recorte criado', exact=True).wait_for(timeout=60000)
        crop_result = crop_response.value.json()
        analysis_id = crop_result['analise']['id']
        wait_for_tiles(page, f'/api/analises/{analysis_id}/tile/')
        page.locator('.layer-item').first.get_by_title('Ocultar camada').click()
        page.screenshot(path=str(OUT / '03_recorte_resultado.png'))
        page.get_by_role('tab', name='Exp').click()
        panel = page.locator('.tools-panel')
        page.locator('.tool-form .p-select:visible').first.click()
        page.get_by_role('option', name='Recorte - Aukerman - ortofoto ODM real', exact=True).last.click()
        page.keyboard.press('Escape')
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / '04_exportacao_configurada.png'))
        with page.expect_download(timeout=60000) as download_info:
            panel.get_by_role('button', name='Exportar', exact=True).click()
        download = download_info.value
        assert download.suggested_filename.endswith('.tif')
        download.save_as(str(OUT / 'recorte_exportado.tif'))
        page.screenshot(path=str(OUT / '05_exportacao_concluida.png'))
        context.close()
        browser.close()
