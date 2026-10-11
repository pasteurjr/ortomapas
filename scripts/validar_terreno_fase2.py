"""Real DSM/DTM browser evidence: geometry, canvas pixels, orbit, wireframe, tablet."""
import base64
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/validacao/terreno_fase2_2026-10-10"
UI = "http://127.0.0.1:5302"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"accepted": False, "errors": [], "screens": [], "canvas_checks": []}
    output = OUT / "resultado.json"
    output.write_text(json.dumps(result))
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.set_default_timeout(60000)
        page.on("pageerror", lambda err: result["errors"].append(str(err)))
        page.on("response", lambda r: print('HTTP', r.status, r.url.split('?')[0]) if '/api/odm/' in r.url else None)
        page.goto(UI, wait_until="networkidle")
        page.locator('input[type=email]').fill('phase1-1791391595@example.test')
        page.locator('input[type=password]').fill('fase1-senha-segura')
        page.get_by_role('button', name='Entrar', exact=True).click()
        page.locator('.project-selector').click()
        page.get_by_role('option', name='Teste PostgreSQL UI', exact=True).click()
        page.locator('.ortomapa-card').filter(has_text='ODM ortomosaico f7563d3d').get_by_title('Visibilidade', exact=True).click()
        page.wait_for_function("""() => { const images = [...document.querySelectorAll('.leaflet-tile-pane img')].filter(i => i.src.includes('/api/ortomapas/')); return images.length > 0 && images.every(i => i.complete && i.naturalWidth === 256 && getComputedStyle(i).opacity === '1') }""")
        page.locator('.workspace-sidebar-nav').get_by_text('Voos e ODM', exact=True).click()
        page.screenshot(path=str(OUT / 'diagnostico_antes_produtos.png'))
        try:
            page.get_by_role('button', name='DSM 3D', exact=True).wait_for()
        except Exception:
            page.screenshot(path=str(OUT / 'erro_final.png'))
            raise
        def capture(label):
            filename = label + '.png'
            page.screenshot(path=str(OUT / filename))
            result['screens'].append(filename)
        capture('01_produtos_reais')
        def pixels():
            canvas = page.locator('.surface-view canvas')
            raw = canvas.evaluate("c => c.toDataURL('image/png').split(',')[1]")
            arr = np.asarray(Image.open(io.BytesIO(base64.b64decode(raw))).convert('RGB'))
            visible = np.any(np.abs(arr.astype(int) - np.array([16,24,32])) > 10, axis=2)
            coverage = float(visible.mean())
            assert coverage > .02, f'Canvas empty or poorly framed: {coverage}'
            return arr, coverage
        def open_surface(name):
            page.get_by_role('button', name=name, exact=True).click()
            page.locator('.surface-view').wait_for()
            page.get_by_text('Carregando DSM...', exact=True).wait_for(state='detached')
            assert not page.locator('.surface-view [role=alert]').count()
            page.wait_for_function("document.querySelector('.surface-view footer').textContent.includes('triangulos') && document.querySelector('.surface-view canvas').width > 500")
            page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        open_surface('DSM 3D')
        arr, coverage = pixels(); result['canvas_checks'].append({'state':'DSM', 'coverage':coverage})
        capture('02_dsm_real_3d')
        canvas = page.locator('.surface-view canvas'); box = canvas.bounding_box()
        page.mouse.move(box['x'] + box['width']*.4, box['y'] + box['height']*.5)
        page.mouse.down(); page.mouse.move(box['x'] + box['width']*.62, box['y'] + box['height']*.62, steps=20); page.mouse.up()
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        rotated, coverage = pixels()
        delta = float(np.abs(rotated.astype(int)-arr.astype(int)).mean())
        assert delta > 1, 'Orbit did not change rendered pixels'
        result['orbit_pixel_difference'] = delta
        capture('03_dsm_orbita')
        page.get_by_title('Alternar wireframe').click()
        assert page.get_by_title('Alternar wireframe').get_attribute('aria-pressed') == 'true'
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        wire, coverage = pixels(); result['canvas_checks'].append({'state':'wireframe', 'coverage':coverage})
        assert float(np.abs(wire.astype(int)-rotated.astype(int)).mean()) > 1
        capture('04_dsm_wireframe')
        page.get_by_title('Alternar wireframe').click()
        page.set_viewport_size({'width':1024,'height':768})
        page.wait_for_function("document.querySelector('.surface-view canvas').width < 1000")
        page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
        _, coverage = pixels(); result['canvas_checks'].append({'state':'tablet', 'coverage':coverage})
        capture('05_dsm_tablet')
        page.get_by_title('Fechar', exact=True).click()
        page.set_viewport_size({'width':1440,'height':900})
        open_surface('DTM 3D')
        _, coverage = pixels(); result['canvas_checks'].append({'state':'DTM', 'coverage':coverage})
        capture('06_dtm_real_3d')
        result['accepted'] = not result['errors']
        output.write_text(json.dumps(result, indent=2), encoding='utf-8')
        browser.close()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
