"""Playwright flow for UC-009 RGB change detection with real API/PostgreSQL.

Prerequisite: run scripts/seed_uc009_change_fixture.py. E2E uses a short-lived
application-signed JWT for the local validation account; it is never printed
or written to disk. No LLM, ODM, or external API is called.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from shutil import which

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright
from backend.database.connection import get_connection
from backend.routers.auth import _token

MANIFEST_PATH = ROOT / "data/ortomapas/uc009_controlled/manifest.json"
OUT_DIR = ROOT / "docs/validacao/ortomapas_conclusao/etapa-09/playwright/uc009_rgb"
BASE_URL = "http://127.0.0.1:5176"
API_URL = "http://127.0.0.1:8888"


def main():
    fixture = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nome,email,perfil,ativo FROM usuarios WHERE id=60 AND ativo=TRUE")
        user = cur.fetchone()
        cur.execute("SELECT id,nome FROM projetos WHERE id=%s", (fixture["project_id"],))
        project = cur.fetchone()
    if not user or not project:
        raise RuntimeError("Conta ou projeto de fixture ausente")
    token = _token(user)
    errors = []
    console_errors = []
    api_responses = []
    page_text = {}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path=which("google-chrome"),
                                             args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1660, "height": 1080}, device_scale_factor=1)
        context.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
        page = context.new_page()
        page.on("pageerror", lambda exc: errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("response", lambda response: api_responses.append({
            "status": response.status, "url": response.url.split("?")[0]
        }) if "/api/tools/changes/ortomosaicos" in response.url or "/api/analises/" in response.url else None)

        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_selector(".app-layout", timeout=30000)
        project_select = page.locator(".project-selector")
        project_select.click()
        page.get_by_role("option", name=project["nome"], exact=True).click()
        page.wait_for_function("document.body.innerText.includes('UC-009 antes')", timeout=30000)
        page_text["project"] = project["nome"]
        page.screenshot(path=str(OUT_DIR / "01_projeto_com_dois_ortomosaicos.png"), full_page=True)

        page.get_by_role("button", name="Análises").click()
        page.get_by_role("tab", name="Mud").click()
        page.wait_for_function("document.body.innerText.includes('Detectar mudanças RGB')", timeout=10000)
        before_text = page.locator(".tools-panel .form-group").nth(1).inner_text()
        after_text = page.locator(".tools-panel .form-group").nth(2).inner_text()
        page_text["before_selector"] = before_text
        page_text["after_selector"] = after_text
        page_text["threshold_control"] = page.locator(".tools-panel .form-group").nth(3).inner_text()
        page.screenshot(path=str(OUT_DIR / "02_uc009_formulario_antes_depois_limiar.png"), full_page=True)

        page.get_by_role("button", name="Detectar mudanças RGB").click()
        page.get_by_text("Mudança RGB detectada", exact=True).wait_for(timeout=120000)
        page.wait_for_timeout(1200)
        stats_rows = [text.strip() for text in page.locator(".change-result .stat-row").all_inner_texts()]
        page_text["statistics"] = stats_rows
        page.screenshot(path=str(OUT_DIR / "03_uc009_mascara_rgb_e_resultado.png"), full_page=True)
        tiles = page.locator(".leaflet-tile-loaded").count()
        manifest = {
            "generated_at": datetime.now().astimezone().isoformat(),
            "project_id": fixture["project_id"],
            "before_product_id": fixture["before_product_id"],
            "after_product_id": fixture["after_product_id"],
            "user_id": user["id"],
            "ui": page_text,
            "expected": {"changed_pixels": fixture["expected_changed_pixels"],
                         "changed_area_m2": fixture["expected_changed_area_m2"],
                         "known_patch": fixture["known_change_window_zero_based"],
                         "threshold_normalized": 0.15},
            "result_tile_images_loaded": tiles,
            "api_responses": api_responses,
            "page_errors": errors,
            "console_errors": console_errors,
            "llm_calls": 0,
        }
        (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        assert any("10.000" in value or "10,000" in value for value in stats_rows), stats_rows
        assert any("25 m²" in value or "25 m2" in value or "25,00" in value or "25.00" in value for value in stats_rows), stats_rows
        assert errors == [], errors
        assert any(item["status"] == 200 and "/api/tools/changes/ortomosaicos" in item["url"] for item in api_responses)
        browser.close()
    print(json.dumps({"screenshots": [str(path.relative_to(ROOT)) for path in sorted(OUT_DIR.glob("*.png"))],
                      "manifest": str((OUT_DIR / "manifest.json").relative_to(ROOT)),
                      "statistics_rows": page_text.get("statistics"), "tiles": tiles,
                      "page_errors": errors}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
