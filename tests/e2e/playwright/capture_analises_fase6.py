"""Capture real persisted analysis results in the Ortomapas web UI (read-only)."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from io import BytesIO

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    fallback = Path.home() / "anaconda3/envs/copa2026/lib/python3.11/site-packages"
    sys.path.insert(0, str(fallback))
    from playwright.sync_api import sync_playwright

from backend.database.connection import get_connection
from backend.routers.auth import _token, active_user

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-06"
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176")
PROJECT_ID = 62
ANALYSIS_IDS = [120, 130, 131, 132, 133, 143, 63, 81]
EXPECTED_TABS = {120: "Cls", 130: "Ter", 131: "Ter", 132: "Ter", 133: "Ter",
                 143: "Hid", 63: "Vol", 81: "Mud"}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM usuarios WHERE perfil='admin' AND ativo=true ORDER BY id LIMIT 1")
        user = active_user(cur.fetchone()["id"])
        token = _token(user)
        cur.execute("SELECT id,nome,tipo_analise FROM analises WHERE id=ANY(%s) ORDER BY id", (ANALYSIS_IDS,))
        records = {r["id"]: dict(r) for r in cur.fetchall()}
        cur.execute("SELECT nome FROM projetos WHERE id=%s", (PROJECT_ID,))
        project_name = cur.fetchone()["nome"]

    targets = [120, 130, 131, 132, 133, 143, 63, 81]
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True,
            executable_path=os.getenv("CHROME_PATH", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        for analysis_id in targets:
            page = browser.new_page(viewport={"width": 1680, "height": 1050})
            errors = []
            tile_status = []
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.on("response", lambda response, aid=analysis_id: tile_status.append(response.status)
                    if f"/analises/{aid}/tile/" in response.url else None)
            page.add_init_script(f"localStorage.setItem('ortomapas_token',{json.dumps(token)})")
            page.goto(UI, wait_until="domcontentloaded")
            project = page.locator(".project-item").filter(has_text=project_name)
            project.wait_for(timeout=30000)
            project.click()
            page.locator(".workspace-sidebar-nav").get_by_text("Análises", exact=True).click()
            result_row = page.locator(f'.result-item[data-analysis-id="{analysis_id}"]')
            result_row.wait_for(timeout=30000)
            initial = np.asarray(Image.open(BytesIO(page.locator(".map-area").screenshot())).convert("RGB"))
            result_row.click()
            active_tab = page.locator('[role="tab"][aria-selected="true"]').inner_text().strip()
            if EXPECTED_TABS[analysis_id] not in active_tab:
                raise AssertionError(f"A análise {analysis_id} não selecionou sua ferramenta: {active_tab!r}")
            deadline = time.time() + 45
            while time.time() < deadline:
                layer = page.locator(".layer-item").filter(has_text=records[analysis_id]["nome"])
                if layer.count() and (tile_status or analysis_id == 133):
                    break
                page.wait_for_timeout(250)
            layer = page.locator(".layer-item").filter(has_text=records[analysis_id]["nome"])
            layer.wait_for(timeout=10000)
            page.wait_for_timeout(1300)
            final = np.asarray(Image.open(BytesIO(page.locator(".map-area").screenshot())).convert("RGB"))
            changed = int(np.count_nonzero(np.any(initial != final, axis=2)))
            if changed < 1000:
                raise AssertionError(f"Camada da análise {analysis_id} não alterou visivelmente o mapa ({changed} px)")
            if analysis_id != 133 and not tile_status:
                raise AssertionError(f"Sem tiles HTTP observados para análise {analysis_id}")
            if tile_status and any(status != 200 for status in tile_status):
                raise AssertionError(f"Tile com status inesperado na análise {analysis_id}: {tile_status}")
            filename = f"ui_analise_{analysis_id}.png"
            page.screenshot(path=str(OUT / filename), full_page=True, animations="disabled")
            results.append({"analysis_id": analysis_id, "name": records[analysis_id]["nome"],
                "type": records[analysis_id]["tipo_analise"], "screenshot": filename,
                "tile_statuses": tile_status, "map_pixels_changed": changed,
                "browser_errors": errors, "visible_layer": layer.inner_text(),
                "active_tool_tab": active_tab})
            page.close()
        browser.close()
    manifest = {"status": "passed", "project_id": PROJECT_ID, "project": project_name,
                "read_only_ui_flow": True, "captures": results}
    (OUT / "playwright.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
