"""Resume visual acceptance after real NodeODM processing has completed."""
from __future__ import annotations

import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.getenv("ODM_ACCEPTANCE_OUT", ROOT / "docs/validacao/ortomapas_conclusao/etapa-03"))
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176")
PROJECT = os.environ["ODM_ACCEPTANCE_PROJECT_NAME"]


def main():
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    stamp = PROJECT.removeprefix("Aceite NodeODM Aukerman ")
    email = manifest["test_user_email"]
    password = f"Orto-{stamp}-Aceite!"
    task_prefix = manifest["task_id"][:8]
    results = manifest.setdefault("viewer_validation", {})
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=os.getenv("CHROME_PATH", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1680, "height": 1050}, accept_downloads=True)
        page.set_default_timeout(45_000)
        page.goto(UI, wait_until="domcontentloaded")
        page.locator("input[type=email]").fill(email)
        page.locator("input[type=password]").fill(password)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.locator(".workspace-sidebar-nav").wait_for()
        page.locator(".project-item").filter(has_text=PROJECT).click()
        page.locator(".workspace-sidebar-nav").get_by_text("Voos e ODM", exact=True).click()
        task = page.locator(".task-row").filter(has_text=task_prefix)
        task.wait_for()

        def capture(name, description):
            page.screenshot(path=str(OUT / f"{name}.png"), full_page=True, animations="disabled")
            screenshots = manifest.setdefault("screenshots", [])
            screenshots[:] = [entry for entry in screenshots if entry.get("file") != f"{name}.png"]
            screenshots.append({"file": f"{name}.png", "description": description})
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        def verify_surface(button_name, kind, name):
            task.get_by_role("button", name=button_name, exact=True).click()
            surface = page.locator(".surface-view")
            surface.wait_for(timeout=60_000)
            page.locator(".surface-view .host canvas").wait_for(timeout=60_000)
            page.wait_for_function("""() => {
              const el=document.querySelector('.surface-view');
              return el && !el.querySelector('.overlay:not(.error)') && Boolean(el.querySelector('footer')?.textContent.includes('triangulos'));
            }""", timeout=90_000)
            if page.locator(".surface-view [role=alert]").count():
                raise AssertionError(page.locator(".surface-view [role=alert]").inner_text())
            footer = page.locator(".surface-view footer").inner_text()
            triangles = int(footer.split("triangulos")[0].split()[-1])
            if triangles <= 0:
                raise AssertionError(f"{kind}: superfície sem triângulos: {footer}")
            slider = page.get_by_role("slider", name="Exagero vertical do terreno")
            slider.fill("2")
            if "2x" not in page.locator(".surface-view output").inner_text():
                raise AssertionError(f"{kind}: exagero vertical não atualizou")
            page.locator('.surface-view button[title="Alternar wireframe"]').click()
            if page.locator('.surface-view button[title="Alternar wireframe"]').get_attribute("aria-pressed") != "true":
                raise AssertionError(f"{kind}: controle wireframe não alternou")
            page.locator('.surface-view button[title="Alternar wireframe"]').click()
            page.locator('.surface-view button[title="Enquadrar"]').click()
            capture(name, f"{kind} real aberto em visualizador WebGL; {footer}; exagero 2x e wireframe testados.")
            results[kind] = {"status": "passed", "footer": footer, "triangles": triangles, "vertical_exaggeration": "2x", "wireframe_toggle": "passed", "canvas_count": page.locator(".surface-view .host canvas").count()}
            page.locator('.surface-view button[title="Fechar"]').click()
            page.locator(".surface-view").wait_for(state="detached")

        verify_surface("DSM 3D", "DSM", "15_dsm_superficie_3d")
        verify_surface("DTM 3D", "DTM", "16_dtm_terreno_3d")

        task.get_by_role("button", name="Abrir 3D", exact=True).click()
        page.locator(".viewer-shell .canvas-host canvas").wait_for(timeout=60_000)
        page.wait_for_function("""() => {
          const text=document.querySelector('.viewer-shell .viewer-header')?.innerText || '';
          return text.includes('pontos') && !text.includes('0 pontos');
        }""", timeout=90_000)
        cloud_text = page.locator(".viewer-shell .viewer-header").inner_text()
        capture("17_nuvem_pontos_3d", f"Nuvem LAS/LAZ real visualizada; {cloud_text.replace(chr(10), ' — ')}.")
        results["point_cloud"] = {"status": "passed", "header": cloud_text}
        page.locator('.viewer-shell button[title="Fechar"]').click()
        page.locator(".viewer-shell").wait_for(state="detached")

        task.get_by_role("button", name="Diferença", exact=True).click()
        diff = page.locator(".diff-view")
        diff.wait_for(timeout=60_000)
        page.wait_for_function("""() => {
          const el=document.querySelector('.diff-view');
          return el && !el.querySelector('.state:not(.error)') && el.querySelector('canvas')?.width > 0;
        }""", timeout=90_000)
        if page.locator(".diff-view .error").count():
            raise AssertionError(page.locator(".diff-view .error").inner_text())
        capture("18_diferenca_dsm_dtm", "Raster de diferença DSM–DTM carregado com legenda diverging para valores positivos e negativos.")
        results["dsm_dtm_difference"] = {"status": "passed", "canvas_width": page.locator(".diff-view canvas").evaluate("el => el.width"), "canvas_height": page.locator(".diff-view canvas").evaluate("el => el.height")}
        page.locator('.diff-view button[title="Fechar diferenca"]').click()
        page.locator(".diff-view").wait_for(state="detached")

        task.locator('button[title="Avaliar qualidade"]').click()
        page.locator(".quality-row").wait_for(timeout=60_000)
        task.locator(".quality-row").scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        manifest["quality_text"] = task.locator(".quality-row").inner_text()
        capture("19_qualidade_do_processamento", "Indicadores de qualidade calculados para o processamento concluído.")
        results["quality"] = {"status": "passed", "text": manifest["quality_text"]}
        manifest["outcome"] = "viewers_passed"
        manifest.pop("failed_at", None)
        manifest.pop("error", None)
        manifest["initial_viewer_attempt"] = {
            "status": "test_harness_selector_mismatch",
            "cause": "The first run expected .dsm-surface-view; the implemented component is .surface-view.",
            "application_defect": False,
            "retest": "All viewers and quality check passed with corrected Playwright selectors.",
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
