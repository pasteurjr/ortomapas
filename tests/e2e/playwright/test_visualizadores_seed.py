"""Captura os viewers ODM/3D usando o projeto seed de Guarajuba."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "runtime/screenshots/demonstracao_video" / ("odm-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.set_default_timeout(12000)
    result = {"status": "passed", "scenes": []}
    try:
        page.goto(os.getenv("FRONTEND_URL", "http://127.0.0.1:5300"), wait_until="networkidle")
        page.locator("input[type=email]").fill(os.getenv("E2E_EMAIL", "phase1-1791391595@example.test"))
        page.locator("input[type=password]").fill(os.getenv("E2E_PASSWORD", "fase1-senha-segura"))
        page.get_by_role("button", name="Entrar").click()
        project = page.get_by_text("Guarajuba - Condomínio Paraíso (Demonstração)", exact=True)
        project.wait_for(); project.click(); page.wait_for_timeout(1000)
        page.locator(".workspace-nav").get_by_text("Voos e ODM", exact=True).click()
        page.locator(".odm-tasks").wait_for()
        def capture(name, title):
            path = OUT / f"{name}.png"; page.screenshot(path=str(path)); result["scenes"].append({"id": name, "title": title, "screenshot": path.name})
        capture("01_odm_pipeline", "Pipeline ODM com estados")
        page.locator(".task-actions button").nth(0).click(); page.locator(".viewer-shell").wait_for(); capture("02_nuvem_pontos_3d", "Nuvem de pontos 3D")
        page.get_by_title("Fechar").click()
        page.locator(".task-actions button").nth(1).click(); page.locator(".surface-view").wait_for(); capture("03_dsm_3d", "Superfície DSM 3D")
        page.get_by_title("Fechar").click()
        page.locator(".task-actions button").nth(2).click(); page.locator(".diff-view").wait_for(); capture("04_diferenca_dsm_dtm", "Diferença DSM-DTM")
        page.get_by_title("Fechar").click()
        page.get_by_title("Avaliar qualidade").click(); page.locator(".quality-row").first.wait_for(); capture("05_qualidade_odm", "Avaliação de qualidade")
    except Exception as exc:
        result["status"] = "failed"; result["error"] = str(exc)
    finally:
        (OUT / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
print(json.dumps({"status": result["status"], "output": str(OUT), "scenes": len(result["scenes"])}))
