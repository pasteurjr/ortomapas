"""Exercise UC-020 RGB-change and volume queue flows with retained ODM rasters.

Data: public Aukerman ODM project #88 (same source photos, two parameter runs).
This validates application/queue wiring, not independent temporal truth or survey accuracy.
"""
from __future__ import annotations

import json
import io
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import rasterio
from PIL import Image
from pyproj import Transformer
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from backend.database.connection import get_connection
from backend.routers.auth import _token

API, UI = "http://127.0.0.1:8888", "http://127.0.0.1:5176"
PROJECT_ID, USER_ID = 88, 60
ORTHO_BEFORE, ORTHO_AFTER, DSM_ID = 70, 75, 71
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-10/uc020_queue_coverage"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")


def record(manifest: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def capture(page, manifest, name, meaning):
    filename = name + ".png"
    page.screenshot(path=str(OUT / filename), full_page=True, animations="disabled")
    manifest["screenshots"].append({"file": filename, "meaning": meaning})
    record(manifest)


def verify_result_tile(page, analysis_id, token, result_path, filename):
    world = 20037508.342789244
    zoom = 16
    with rasterio.open(result_path) as raster:
        center_x = (raster.bounds.left + raster.bounds.right) / 2
        center_y = (raster.bounds.bottom + raster.bounds.top) / 2
        mercator_x, mercator_y = Transformer.from_crs(raster.crs, "EPSG:3857", always_xy=True).transform(center_x, center_y)
    span = 2 * world / (2 ** zoom)
    x = int((mercator_x + world) // span)
    y = int((world - mercator_y) // span)
    response = page.request.get(f"{API}/api/analises/{analysis_id}/tile/{zoom}/{x}/{y}.png",
                                headers={"Authorization": f"Bearer {token}"})
    assert response.status == 200, {"tile": [zoom, x, y], "status": response.status, "body": response.text()[:200]}
    image = Image.open(io.BytesIO(response.body())).convert("RGBA")
    alpha_pixels = int((image.getchannel("A").point(lambda value: 255 if value else 0)).histogram()[255])
    output = OUT / filename
    image.save(output)
    assert image.size == (256, 256) and alpha_pixels > 0, {"size": image.size, "alpha_pixels": alpha_pixels}
    return {"http_status": response.status, "zxy": [zoom, x, y], "size": list(image.size),
            "opaque_pixels": alpha_pixels, "file": filename}


def main():
    api_process = None
    try:
        with urlopen(API + "/health", timeout=2):
            pass
    except (URLError, TimeoutError):
        log = open("/tmp/ortomapas-uc020-api-e2e.log", "w", encoding="utf-8")
        api_process = subprocess.Popen([str(ROOT / ".conda-env/bin/python"), "-m", "uvicorn",
                                        "backend.main:app", "--host", "127.0.0.1", "--port", "8888"],
                                       cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                       start_new_session=True)
        for _ in range(30):
            try:
                with urlopen(API + "/health", timeout=2):
                    break
            except (URLError, TimeoutError):
                time.sleep(1)
        else:
            api_process.terminate()
            raise RuntimeError("A API não iniciou para a validação integrada")
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,email,nome,perfil,ativo FROM usuarios WHERE id=%s", (USER_ID,))
        user = cur.fetchone()
        cur.execute("SELECT id,nome FROM projetos WHERE id=%s", (PROJECT_ID,))
        project = cur.fetchone()
        cur.execute("SELECT id,nome,tipo,caminho_arquivo FROM ortomapas WHERE id=ANY(%s) ORDER BY id",
                    ([ORTHO_BEFORE, ORTHO_AFTER, DSM_ID],))
        assets = cur.fetchall()
    if not user or not user["ativo"] or not project or len(assets) != 3:
        raise RuntimeError("Usuário, projeto ou produtos públicos de validação indisponíveis")
    token = _token(user)
    manifest = {
        "date": datetime.now().astimezone().isoformat(), "case": "UC-020 / mudança RGB e volume enfileirados",
        "scope": "API, PostgreSQL, worker, resultado persistido e interface Playwright; sem Copiloto/LLM",
        "data": {"origin": "Aukerman público, licença CC0, já processado no projeto #88",
                 "limitation": "As duas ortofotos vêm das mesmas 77 imagens, em dois processamentos; não são campanhas temporais independentes.",
                 "project_id": PROJECT_ID, "products": [{"id": x["id"], "name": x["nome"], "type": x["tipo"]} for x in assets]},
        "profile": {"user_id": USER_ID, "role": user["perfil"]},
        "operations": [], "screenshots": [], "browser_errors": [], "llm_calls": 0,
    }
    analysis_ids = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path="/usr/bin/google-chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 1000})
        page.set_default_timeout(30_000)
        page.on("pageerror", lambda exc: manifest["browser_errors"].append(str(exc)))
        page.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
        page.goto(UI, wait_until="networkidle")
        assert page.request.get(API + "/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status == 200
        page.get_by_text(project["nome"], exact=True).first.click()
        page.locator(".workspace-sidebar-nav .workspace-nav-item").filter(has_text="Análises").click()
        page.locator(".leaflet-container").wait_for()

        # UC-009 analysis, now running inside the UC-020 worker queue.
        page.locator('.status-btn[title="Nova Analise"]').click()
        modal = page.locator(".modal")
        selects = modal.locator("select")
        selects.nth(0).select_option(str(ORTHO_AFTER))
        selects.nth(1).select_option("deteccao_mudancas")
        selects.nth(2).select_option(str(ORTHO_BEFORE))
        modal.locator('input[placeholder*="NDVI Fazenda Norte"]').fill(f"UC020 mudança RGB {STAMP}")
        queue = modal.locator('input[type="checkbox"]')
        assert queue.count() == 1 and modal.get_by_text("Enviar para fila de processamento", exact=True).is_visible()
        queue.check()
        capture(page, manifest, "01_mudanca_formulario_enfileirar", "Formulário com dois ortomosaicos do mesmo projeto, limiar e fila habilitada.")
        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/api/analises")) as pending:
            modal.get_by_role("button", name="Criar e Executar").click()
        response = pending.value
        body = response.json()
        assert response.status == 202, {"status": response.status, "body": body}
        change_id = int(body["id"]); analysis_ids.append(change_id)
        change = {"case": "UC-009 + UC-020", "analysis_id": change_id, "task_id": body["tarefa_id"],
                  "post_status": response.status, "expected": "202, em_fila/processando → concluida, máscara persistida e comparação temporal criada."}
        for _ in range(300):
            latest = page.request.get(f"{API}/api/analises/{change_id}", headers={"Authorization": f"Bearer {token}"}).json()
            if latest.get("status") in {"concluida", "erro"}:
                break
            page.wait_for_timeout(1000)
        assert latest.get("status") == "concluida", latest
        assert latest.get("resultado_path") and latest.get("resultado", {}).get("stats"), latest
        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id,status,agente FROM tarefas_agentes WHERE id=%s", (body["tarefa_id"],))
            change_task = cur.fetchone()
            cur.execute("SELECT count(*) AS n FROM comparacoes_temporais WHERE resultado_path=%s", (latest["resultado_path"],))
            comparison_count = int(cur.fetchone()["n"])
        assert change_task and change_task["status"] == "concluido" and change_task["agente"] == "agente_mudanca_fila"
        assert comparison_count == 1
        change["tile"] = verify_result_tile(page, change_id, token, latest["resultado_path"], "tile_mudanca_rgb.png")
        change.update({"status": latest["status"], "queue_status": change_task["status"],
                      "agent": change_task["agente"], "result_path_present": True,
                      "statistics": latest["resultado"]["stats"], "comparison_records": comparison_count})
        manifest["operations"].append(change); record(manifest)
        page.locator('.status-btn[title="Atualizar"]').click()
        row = page.locator(f'.result-item[data-analysis-id="{change_id}"]')
        row.wait_for(timeout=15_000)
        row.click()
        page.locator(".layer-control-item").filter(has_text="Mudanca RGB entre ortomosaicos").wait_for(timeout=15_000)
        page.locator(".stats-panel").wait_for(timeout=15_000)
        change["map_layer_visible"] = True
        change["statistics_panel_visible"] = True
        capture(page, manifest, "02_mudanca_concluida_mapa", "Máscara RGB selecionada no catálogo e exibida como resultado no mapa.")

        # UC-012 volume in relation to a stated elevation, using a real DSM.
        page.locator('.status-btn[title="Nova Analise"]').click()
        modal = page.locator(".modal")
        selects = modal.locator("select")
        selects.nth(0).select_option(str(DSM_ID))
        selects.nth(1).select_option("calculo_volume")
        modal.locator('input[placeholder*="NDVI Fazenda Norte"]').fill(f"UC020 volume cota 241m {STAMP}")
        modal.locator('input[type="number"]').first.fill("241")
        queue = modal.locator('input[type="checkbox"]')
        assert queue.count() == 1
        queue.check()
        capture(page, manifest, "03_volume_formulario_enfileirar", "Formulário com DSM #71, cota de referência 241 m e fila habilitada.")
        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/api/analises")) as pending:
            modal.get_by_role("button", name="Criar e Executar").click()
        response = pending.value; body = response.json()
        assert response.status == 202, {"status": response.status, "body": body}
        volume_id = int(body["id"]); analysis_ids.append(volume_id)
        volume = {"case": "UC-012 + UC-020", "analysis_id": volume_id, "task_id": body["tarefa_id"],
                  "post_status": response.status, "input": {"dsm_id": DSM_ID, "reference_elevation_m": 241.0},
                  "expected": "202, tarefa terminal concluída, raster de diferença e estatísticas de corte/aterro persistidos."}
        for _ in range(300):
            latest = page.request.get(f"{API}/api/analises/{volume_id}", headers={"Authorization": f"Bearer {token}"}).json()
            if latest.get("status") in {"concluida", "erro"}:
                break
            page.wait_for_timeout(1000)
        assert latest.get("status") == "concluida", latest
        assert latest.get("tipo_analise") == "volume" and latest.get("resultado_path"), latest
        stats = latest.get("resultado", {}).get("stats", {})
        assert stats.get("valid_pixels", 0) > 0 and stats.get("valid_area_m2", 0) > 0, stats
        volume["tile"] = verify_result_tile(page, volume_id, token, latest["resultado_path"], "tile_volume.png")
        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id,status,agente FROM tarefas_agentes WHERE id=%s", (body["tarefa_id"],))
            volume_task = cur.fetchone()
        assert volume_task and volume_task["status"] == "concluido" and volume_task["agente"] == "agente_mudanca_fila"
        volume.update({"status": latest["status"], "queue_status": volume_task["status"],
                       "agent": volume_task["agente"], "result_path_present": True,
                       "statistics": stats})
        manifest["operations"].append(volume); record(manifest)
        page.locator('.status-btn[title="Atualizar"]').click()
        row = page.locator(f'.result-item[data-analysis-id="{volume_id}"]')
        row.wait_for(timeout=15_000)
        row.click()
        page.locator(".layer-control-item").filter(has_text="Corte/aterro por cota").wait_for(timeout=15_000)
        page.locator(".stats-panel").wait_for(timeout=15_000)
        volume["map_layer_visible"] = True
        volume["statistics_panel_visible"] = True
        capture(page, manifest, "04_volume_concluido_mapa", "Raster de corte/aterro selecionado e estatísticas do resultado exibidas na interface.")
        manifest["result"] = "PASS" if not manifest["browser_errors"] else "PASS_WITH_BROWSER_ERRORS"
        browser.close()
    record(manifest)
    if api_process:
        api_process.terminate()
        api_process.wait(timeout=15)
    print(json.dumps({"result": manifest["result"], "manifest": str(OUT / "manifest.json"),
                      "analysis_ids": analysis_ids, "operations": manifest["operations"]}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
