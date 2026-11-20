"""End-to-end UC-009 comparison using independent 2022/2024 UAV campaigns."""
from __future__ import annotations

import io
import json
import atexit
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import rasterio
import numpy as np
from PIL import Image
from pyproj import CRS, Transformer
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from backend.database.connection import get_connection
from backend.routers.auth import _token

API = "http://127.0.0.1:8888"
UI = "http://127.0.0.1:5176"
USER_ID = 60
MANIFEST = ROOT / "docs/validacao/ortomapas_conclusao/etapa-10/uc009_independent_campaigns/seed_manifest.json"
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-10/uc009_independent_campaigns"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")


def service_ready(url: str) -> bool:
    try:
        with urlopen(url, timeout=2):
            return True
    except (URLError, TimeoutError):
        return False


def verify_tile(page, analysis_id: int, token: str, raster_path: str) -> dict:
    world = 20037508.342789244
    zoom = 12
    with rasterio.open(raster_path) as src:
        x0, y0 = (src.bounds.left + src.bounds.right) / 2, (src.bounds.bottom + src.bounds.top) / 2
        mx, my = Transformer.from_crs(src.crs, "EPSG:3857", always_xy=True).transform(x0, y0)
    span = 2 * world / (2**zoom)
    x = int((mx + world) // span)
    y = int((world - my) // span)
    response = page.request.get(f"{API}/api/analises/{analysis_id}/tile/{zoom}/{x}/{y}.png",
                                headers={"Authorization": f"Bearer {token}"})
    assert response.status == 200, {"status": response.status, "body": response.text()[:300]}
    image = Image.open(io.BytesIO(response.body())).convert("RGBA")
    opaque = image.getchannel("A").histogram()[255]
    filename = "tile_uc009_mudancas.png"
    image.save(OUT / filename)
    assert image.size == (256, 256) and opaque > 0
    return {"http_status": 200, "zxy": [zoom, x, y], "size": list(image.size),
            "opaque_pixels": opaque, "screenshot": filename}


def radiometry_sample(path: Path) -> dict:
    """Summarize deterministic 512x512 average-resampled RGB previews."""
    with rasterio.open(path) as src:
        rgb = src.read([1, 2, 3], out_shape=(3, 512, 512), resampling=rasterio.enums.Resampling.average)
        valid = src.dataset_mask(out_shape=(512, 512), resampling=rasterio.enums.Resampling.nearest) > 0
    return {"valid_preview_pixels": int(valid.sum()),
            "bands_rgb_p10_p50_p90": [[round(float(v), 3) for v in np.quantile(rgb[band][valid], [0.1, 0.5, 0.9])]
                                      for band in range(3)]}


def main() -> None:
    seed = json.loads(MANIFEST.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    products = seed["campaigns"]
    before, after = products
    before_path, after_path = ROOT / before["local_path"], ROOT / after["local_path"]
    with rasterio.open(before_path) as a, rasterio.open(after_path) as b:
        if CRS.from_user_input(a.crs) != CRS.from_user_input(b.crs):
            raise AssertionError("CRS diferentes entre as campanhas")
        left = max(a.bounds.left, b.bounds.left)
        right = min(a.bounds.right, b.bounds.right)
        bottom = max(a.bounds.bottom, b.bounds.bottom)
        top = min(a.bounds.top, b.bounds.top)
        overlap_area = max(0.0, right - left) * max(0.0, top - bottom)
        area_a = (a.bounds.right - a.bounds.left) * (a.bounds.top - a.bounds.bottom)
        area_b = (b.bounds.right - b.bounds.left) * (b.bounds.top - b.bounds.bottom)
        smaller_area = min(area_a, area_b)
        overlap_ratio = overlap_area / smaller_area
        resolution_a = max(abs(value) for value in a.res)
        resolution_b = max(abs(value) for value in b.res)
        resolution_ratio = abs(resolution_a - resolution_b) / max(resolution_a, resolution_b)
        input_checks = {"crs": a.crs.to_string(), "before_grid": [a.width, a.height],
                        "after_grid": [b.width, b.height], "before_resolution_m": list(a.res),
                        "after_resolution_m": list(b.res), "overlap_ratio_smaller_footprint": overlap_ratio,
                        "resolution_relative_difference": resolution_ratio,
                        "transform_equal": a.transform == b.transform,
                        "alignment_note": "the source dataset reports the 2024 campaign aligned to 2022; application reprojects grids but does not estimate a new image registration.",
                        "before_rgb_preview_quantiles": radiometry_sample(before_path),
                        "after_rgb_preview_quantiles": radiometry_sample(after_path)}
    assert overlap_ratio >= 0.90, input_checks
    assert resolution_ratio <= 0.02, input_checks

    api_process = None
    vite_process = None
    processes = []
    log_files = []
    for url, port, name in ((API + "/health", "8888", "api"), (UI, "5176", "vite")):
        if service_ready(url):
            continue
        logfile = open(f"/tmp/ortomapas-uc009-{name}.log", "w", encoding="utf-8")
        log_files.append(logfile)
        if name == "api":
            api_process = subprocess.Popen([str(ROOT / ".conda-env/bin/python"), "-m", "uvicorn",
                                            "backend.main:app", "--host", "127.0.0.1", "--port", port],
                                           cwd=ROOT, stdout=logfile, stderr=subprocess.STDOUT,
                                           start_new_session=True)
            processes.append(api_process)
        else:
            vite_process = subprocess.Popen([str(ROOT / "frontend/node_modules/.bin/vite"), "--host",
                                             "127.0.0.1", "--port", port], cwd=ROOT / "frontend",
                                            stdout=logfile, stderr=subprocess.STDOUT, start_new_session=True)
            processes.append(vite_process)
        for _ in range(60):
            if service_ready(url):
                break
            time.sleep(1)
        else:
            raise RuntimeError(f"Serviço de validação não iniciou: {name}")
    atexit.register(lambda: [proc.terminate() for proc in processes if proc.poll() is None])

    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nome,perfil,ativo FROM usuarios WHERE id=%s", (USER_ID,))
        user = cur.fetchone()
        cur.execute("SELECT id,nome FROM projetos WHERE id=%s", (seed["project_id"],))
        project = cur.fetchone()
        cur.execute("SELECT id,nome,tipo,voo_id,caminho_arquivo FROM ortomapas WHERE id=ANY(%s) ORDER BY voo_id",
                    ([int(item["product_id"]) for item in products],))
        registered_products = cur.fetchall()
    if not user or not user["ativo"] or not project or len(registered_products) != 2:
        raise RuntimeError("Conta, projeto ou os dois produtos de validação não existem")
    token = _token(user)
    map_tile_responses = []
    report = {"date": datetime.now().astimezone().isoformat(), "case": "UC-009 — campanhas UAV independentes",
              "scope": "enqueue real na aplicação, worker, PostgreSQL, tile autenticado e UI Playwright; sem LLM",
              "project": {"id": project["id"], "name": project["nome"]}, "input_checks": input_checks,
              "source": seed["source"], "products": registered_products,
              "expected": {"post_status": 202, "terminal_status": "concluida",
                           "change_threshold_normalized": 0.15,
                           "map_layer_visible": True, "statistics_panel_visible": True},
              "screenshots": [], "browser_errors": [], "console_errors": [], "llm_calls": 0}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1600, "height": 1400}, device_scale_factor=1)
        page.set_default_timeout(30_000)
        page.on("pageerror", lambda error: report["browser_errors"].append(str(error)))
        page.on("console", lambda msg: report["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.on("response", lambda response: map_tile_responses.append(
            {"status": response.status, "path": response.url.split("?", 1)[0]}
        ) if "/api/analises/" in response.url and
             ("/tile-access" in response.url.split("?", 1)[0] or "/tile/" in response.url.split("?", 1)[0]) else None)
        page.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
        page.goto(UI, wait_until="networkidle")
        assert page.request.get(API + "/api/auth/me", headers={"Authorization": f"Bearer {token}"}).status == 200
        page.get_by_text(project["nome"], exact=True).first.click()
        page.locator(".workspace-sidebar-nav .workspace-nav-item").filter(has_text="Análises").click()
        page.locator(".leaflet-container").wait_for()
        page.locator('.status-btn[title="Nova Analise"]').click()
        modal = page.locator(".modal")
        selects = modal.locator("select")
        selects.nth(0).select_option(str(after["product_id"]))
        selects.nth(1).select_option("deteccao_mudancas")
        selects.nth(2).select_option(str(before["product_id"]))
        modal.locator('input[placeholder*="NDVI Fazenda Norte"]').fill(f"UC009 Aklavik 2022–2024 {STAMP}")
        assert modal.locator('input[type="range"]').input_value() == "0.15"
        assert modal.get_by_text("Compara dois ortomosaicos RGB", exact=False).is_visible()
        modal.locator('input[type="checkbox"]').check()
        shot = "01_formulario_campanhas_antes_depois.png"
        page.screenshot(path=str(OUT / shot), full_page=True, animations="disabled")
        report["screenshots"].append({"file": shot, "meaning": "2024 como depois; 2022 como referência; limiar RGB 0,15; tarefa na fila."})
        with page.expect_response(lambda response: response.request.method == "POST" and response.url.endswith("/api/analises")) as pending:
            modal.get_by_role("button", name="Criar e Executar").click()
        response = pending.value
        assert response.status == 202, {"status": response.status, "body": response.text()[:300]}
        created = response.json()
        analysis_id = int(created["id"])
        report["analysis_id"] = analysis_id
        report["task_id"] = int(created["tarefa_id"])
        latest = None
        for _ in range(3600):
            result = page.request.get(f"{API}/api/analises/{analysis_id}",
                                      headers={"Authorization": f"Bearer {token}"})
            assert result.status == 200, result.text()[:200]
            latest = result.json()
            if latest.get("status") in {"concluida", "erro"}:
                break
            page.wait_for_timeout(1000)
        assert latest and latest.get("status") == "concluida", latest
        assert latest.get("resultado_path") and latest.get("resultado", {}).get("stats"), latest
        raw_stats = latest["resultado"]["stats"]
        scalar_stats = {key: value for key, value in raw_stats.items()
                        if isinstance(value, (int, float)) and key != "histogram"}
        report["analysis"] = {"status": latest["status"], "result_path": latest["resultado_path"],
                               "statistics": scalar_stats,
                               "comparison_parameters": latest.get("parametros")}
        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT status,agente,parametros FROM tarefas_agentes WHERE id=%s", (created["tarefa_id"],))
            task = cur.fetchone()
            cur.execute("SELECT id FROM comparacoes_temporais WHERE resultado_path=%s", (latest["resultado_path"],))
            comparisons = cur.fetchall()
        assert task and task["status"] == "concluido" and task["agente"] == "agente_mudanca_fila", task
        assert len(comparisons) == 1, comparisons
        report["task"] = {"status": task["status"], "agent": task["agente"]}
        report["comparison_record_ids"] = [int(item["id"]) for item in comparisons]
        report["tile"] = verify_tile(page, analysis_id, token, latest["resultado_path"])
        page.locator('.status-btn[title="Atualizar"]').click()
        row = page.locator(f'.result-item[data-analysis-id="{analysis_id}"]')
        row.wait_for(timeout=30_000)
        row.click()
        page.locator(".stats-panel").wait_for(timeout=30_000)
        page.locator(".layer-control-item").filter(has_text="Mudanca RGB entre ortomosaicos").wait_for(timeout=30_000)
        map_tile_images = []
        for _ in range(30):
            map_tile_images = page.locator(".leaflet-tile-loaded").evaluate_all(
                f"els => els.map(el => el.src).filter(src => src.includes('/api/analises/{analysis_id}/tile/'))")
            if map_tile_images:
                break
            page.wait_for_timeout(500)
        assert map_tile_images and map_tile_responses and all(item["status"] == 200 for item in map_tile_responses), {
            "tile_images": len(map_tile_images), "map_tile_responses": map_tile_responses
        }
        report["map_tile_responses"] = map_tile_responses
        report["map_tile_images_loaded"] = len(map_tile_images)
        page.locator(".stats-panel").evaluate("element => element.scrollIntoView({block: 'center'})")
        report["map_layer_visible"] = True
        report["statistics_panel_visible"] = page.locator(".stats-panel").is_visible()
        report["statistics_rows_visible"] = page.locator(".stats-panel .stat-row").count()
        assert report["statistics_panel_visible"] and report["statistics_rows_visible"] >= 2
        report["change_mask_warning_visible"] = page.get_by_text("Máscara de diferença RGB acima do limiar", exact=False).is_visible()
        shot = "02_resultado_mascara_mapa_estatisticas.png"
        page.screenshot(path=str(OUT / shot), full_page=True, animations="disabled")
        report["screenshots"].append({"file": shot, "meaning": "Máscara temporal carregada no mapa, camada ligada e estatísticas do worker exibidas."})
        report["browser_errors_free"] = not report["browser_errors"] and not report["console_errors"]
        report["result"] = "PASS_FUNCTIONAL_SCOPE" if report["browser_errors_free"] else "FAIL_BROWSER_ERRORS"
        browser.close()
    (OUT / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    if api_process:
        api_process.terminate()
        api_process.wait(timeout=15)
        api_process = None
    if vite_process:
        vite_process.terminate()
        vite_process.wait(timeout=15)
        vite_process = None
    for stream in log_files:
        stream.close()
    print(json.dumps({"result": report["result"], "analysis_id": report["analysis_id"],
                      "task_id": report["task_id"], "input_checks": input_checks,
                      "statistics": report["analysis"]["statistics"], "tile": report["tile"],
                      "screenshots": [item["file"] for item in report["screenshots"]]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
