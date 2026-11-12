"""Revalidate viewers for an already processed ODM acceptance project.

This continuation does not upload photos or submit another NodeODM task.
Set ODM_ACCEPTANCE_PASSWORD for the disposable test account before running.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from shutil import which

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-08/ponta-a-ponta"
MANIFEST = OUT / "manifest.json"
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176")


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    email = os.getenv("ODM_ACCEPTANCE_EMAIL") or manifest["test_user_email"]
    password = os.getenv("ODM_ACCEPTANCE_PASSWORD")
    if not password:
        raise RuntimeError("Defina ODM_ACCEPTANCE_PASSWORD para a conta descartável de validação.")

    errors: list[str] = []
    screenshots = manifest.setdefault("resume_screenshots", [])
    task_id = manifest["task_id"]
    project_name = manifest["project_name"]

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=os.getenv("CHROME_PATH") or which("google-chrome") or which("chromium"),
            args=["--no-sandbox"],
        )
        page = browser.new_page(
            viewport={"width": 1680, "height": 1050}, accept_downloads=True
        )
        page.set_default_timeout(45_000)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(UI, wait_until="domcontentloaded")
        page.locator("input[type=email]").fill(email)
        page.locator("input[type=password]").fill(password)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.locator(".workspace-sidebar-nav").wait_for(timeout=60_000)
        page.locator(".project-item").filter(has_text=project_name).click()
        page.locator(".workspace-sidebar-nav").get_by_text("Voos e ODM", exact=True).click()
        task = page.locator(".task-row").filter(has_text=task_id[:8])
        task.wait_for(timeout=60_000)

        def capture(name: str, description: str) -> None:
            page.screenshot(
                path=str(OUT / f"{name}.png"), full_page=True, animations="disabled"
            )
            screenshots[:] = [item for item in screenshots if item.get("file") != f"{name}.png"]
            screenshots.append({"file": f"{name}.png", "description": description})

        task.get_by_role("button", name="Modelo texturizado 3D", exact=True).click()
        page.locator(".model-view .canvas-host").wait_for()
        page.wait_for_function(
            "document.querySelector('.model-view .canvas-host')?.dataset.modelState === 'loaded'",
            timeout=180_000,
        )
        capture(
            "14_modelo_texturizado_3d",
            "Modelo GLB renderizado em WebGL; métricas de malha e materiais visíveis.",
        )
        page.locator('.model-view button[title="Fechar"]').click()
        page.locator(".model-view").wait_for(state="detached")

        for label, filename, description in [
            ("DSM 3D", "16_dsm_superficie_3d_corrigida", "DSM aberto como superfície 3D."),
            ("DTM 3D", "17_dtm_terreno_3d_corrigida", "DTM aberto como terreno 3D."),
        ]:
            task.get_by_role("button", name=label, exact=True).click()
            page.locator(".surface-view").wait_for()
            page.wait_for_timeout(2_500)
            capture(filename, description)
            page.locator('.surface-view button[title="Fechar"]').click()
            page.locator(".surface-view").wait_for(state="detached")

        task.get_by_role("button", name="Abrir 3D", exact=True).click()
        page.locator(".viewer-shell").wait_for()
        page.wait_for_timeout(4_000)
        capture(
            "18_nuvem_pontos_3d",
            "Nuvem LAZ em 3D; contagem total e quantidade de pontos amostrados visíveis.",
        )
        page.locator('.viewer-shell button[title="Fechar"]').click()
        page.locator(".viewer-shell").wait_for(state="detached")

        task.get_by_role("button", name="Diferença", exact=True).click()
        page.locator(".diff-view").wait_for()
        page.wait_for_timeout(2_500)
        capture("19_diferenca_dsm_dtm", "Diferença DSM–DTM com estatísticas e CRS visíveis.")
        page.locator('.diff-view button[title="Fechar diferenca"]').click()
        page.locator(".diff-view").wait_for(state="detached")

        task.locator('button[title="Avaliar qualidade"]').click()
        page.locator(".quality-row").wait_for()
        manifest["quality_text"] = task.locator(".quality-row").inner_text()
        capture("20_qualidade_do_processamento", "Resultado da avaliação ODM visível no cartão da tarefa.")

        manifest["final_viewer_revalidation"] = {
            "status": "passed" if not errors else "failed",
            "browser_page_errors": errors,
            "checked": ["GLB", "DSM", "DTM", "LAZ", "DSM-DTM", "qualidade"],
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "photos_uploaded": False,
            "nodeodm_processing_submitted": False,
        }
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        browser.close()

    if errors:
        raise RuntimeError(f"Erros JavaScript durante visualização: {errors}")
    print(json.dumps(manifest["final_viewer_revalidation"], ensure_ascii=False))


if __name__ == "__main__":
    main()
