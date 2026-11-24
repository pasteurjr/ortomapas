"""Playwright validation of UC-010 against a real Aklavik UAV orthomosaic."""
from __future__ import annotations

import atexit
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.error import URLError
from urllib.request import urlopen

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
API = "http://127.0.0.1:8888"
UI = "http://127.0.0.1:5176"
PROJECT_ID = 90
ORTHO_ID = 81
USER_ID = 60
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-10/uc010_semantic_quality"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")

from backend.database.connection import get_connection
from backend.routers.auth import _token


def ready(url: str) -> bool:
    try:
        with urlopen(url, timeout=2):
            return True
    except (URLError, TimeoutError):
        return False


def services() -> tuple[list[subprocess.Popen], list]:
    processes, logs = [], []
    definitions = [
        (API + "/health", [str(ROOT / ".conda-env/bin/python"), "-m", "uvicorn",
                            "backend.main:app", "--host", "127.0.0.1", "--port", "8888"], ROOT, "api"),
        (UI, [str(ROOT / "frontend/node_modules/.bin/vite"), "--host", "127.0.0.1",
              "--port", "5176"], ROOT / "frontend", "vite"),
    ]
    for url, command, cwd, name in definitions:
        if ready(url):
            continue
        stream = open(f"/tmp/ortomapas-uc010-{name}.log", "w", encoding="utf-8")
        logs.append(stream)
        process = subprocess.Popen(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        processes.append(process)
        for _ in range(90):
            if ready(url):
                break
            time.sleep(1)
        else:
            raise RuntimeError(f"Serviço local não iniciou: {name}")
    atexit.register(lambda: [p.terminate() for p in processes if p.poll() is None])
    return processes, logs


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE id=%s AND ativo=true", (USER_ID,))
        user = cur.fetchone()
        cur.execute("SELECT id,nome FROM projetos WHERE id=%s", (PROJECT_ID,))
        project = cur.fetchone()
        cur.execute("SELECT id,nome,tipo,caminho_arquivo FROM ortomapas WHERE id=%s AND projeto_id=%s",
                    (ORTHO_ID, PROJECT_ID))
        ortho = cur.fetchone()
    if not user or not project or not ortho:
        raise RuntimeError("Conta autorizada, projeto ou ortomosaico de validação não encontrado")
    token = _token(user)
    processes, logs = services()
    record = {
        "date": datetime.now().astimezone().isoformat(),
        "case": "UC-010 — agrupamento K-Means RGB pela UI",
        "scope": "projeto real, ortomosaico UAV real, AOI desenhada na tela, API de produção e persistência PostgreSQL",
        "project": {"id": project["id"], "name": project["nome"]},
        "source": {"id": ortho["id"], "name": ortho["nome"], "type": ortho["tipo"]},
        "expected": {"api_status": 200, "groups": 5, "aoi_required": True,
                     "raster_persisted": True, "semantic_names": False},
        "screenshots": [], "browser_errors": [], "console_errors": [], "tile_responses": [],
    }
    classify_request = {}
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/google-chrome",
                                                  args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=1)
            page.set_default_timeout(25_000)
            page.on("pageerror", lambda error: record["browser_errors"].append(str(error)))
            page.on("console", lambda msg: record["console_errors"].append(msg.text)
                    if msg.type == "error" else None)
            page.on("response", lambda response: record["tile_responses"].append(
                {"status": response.status, "path": response.url.split("?", 1)[0]}
            ) if f"/api/ortomapas/{ORTHO_ID}/tile/" in response.url else None)
            page.on("response", lambda response: record.setdefault("analysis_tile_responses", []).append(
                {"status": response.status, "zxy": response.url.split("/tile/", 1)[-1].split("?", 1)[0]}
            ) if "/api/analises/" in response.url and "/tile/" in response.url else None)
            page.on("request", lambda request: classify_request.update(request.post_data_json)
                    if request.method == "POST" and request.url.endswith("/api/tools/classify") else None)
            page.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
            page.goto(UI, wait_until="networkidle")
            assert page.request.get(API + "/api/auth/me",
                                    headers={"Authorization": f"Bearer {token}"}).status == 200
            page.get_by_text(project["nome"], exact=True).first.click()
            card = page.locator(".ortomapa-card").filter(has_text="campanha 2022")
            card.wait_for()
            visibility_button = card.locator("button[title='Visibilidade']")
            icon_class = visibility_button.locator("i").get_attribute("class") or ""
            if "eye-slash" in icon_class:
                visibility_button.click()
            page.wait_for_function("() => document.querySelectorAll('.leaflet-tile-loaded').length >= 8")
            page.wait_for_timeout(2500)
            source_tile_images = page.locator(".leaflet-tile-loaded").evaluate_all(
                "els => els.map(el => el.src).filter(src => src.includes('/api/ortomapas/'))")
            record["source_tile_images"] = len(source_tile_images)
            if not record["source_tile_images"]:
                raise AssertionError({"visibility_icon": icon_class, "loaded_tile_images": source_tile_images,
                                      "tile_responses": record["tile_responses"]})
            page.get_by_text("Análises", exact=True).click()
            page.get_by_text("Ferramentas espaciais", exact=True).click()
            page.get_by_role("tab", name="Cls").click()
            form = page.locator(".tools-panel")
            form.get_by_text("K-Means RGB (Nao Supervisionado)", exact=False).wait_for()
            shot = "03_ui_projeto_mapa_e_configuracao_uc010.png"
            page.screenshot(path=str(OUT / shot), full_page=True, animations="disabled")
            record["screenshots"].append({"file": shot,
                "meaning": "Projeto real, ortomosaico Aklavik visível e formulário K-Means RGB com cinco grupos."})

            form.get_by_label("Limitar a area").nth(2).check()
            form.locator("button[title='Desenhar area da classificacao']").click()
            form.get_by_text("Desenhando", exact=True).wait_for(timeout=10_000)
            # A small four-vertex AOI over the visible orthomosaic keeps the real-data run bounded.
            draw_points = [(760, 505), (820, 505), (820, 565), (760, 565)]
            for x, y in draw_points:
                page.mouse.move(x, y, steps=5)
                page.mouse.click(x, y, delay=100)
                page.wait_for_timeout(300)
            shot = "04_ui_aoi_em_desenho.png"
            page.screenshot(path=str(OUT / shot), full_page=True, animations="disabled")
            record["screenshots"].append({"file": shot, "meaning": "Quatro vértices da AOI desenhados sobre o ortomosaico real."})
            # The shared completion control is exposed in the crop tab; it finalizes the same AOI.
            page.get_by_role("tab", name="Rec").click()
            page.get_by_role("button", name="Concluir poligono").click()
            page.get_by_role("tab", name="Cls").click()
            if not form.get_by_text("Area selecionada", exact=True).count():
                raise AssertionError({"aoi_status": form.get_by_text("Desenhando", exact=True).count(),
                                      "map_bounds": page.locator(".leaflet-container").bounding_box()})
            form.get_by_text("Area selecionada", exact=True).first.wait_for(timeout=10_000)
            assert form.get_by_role("button", name="Gerar Grupos").is_enabled()
            shot = "05_ui_aoi_selecionada_no_ortomosaico.png"
            page.screenshot(path=str(OUT / shot), full_page=True, animations="disabled")
            record["screenshots"].append({"file": shot,
                "meaning": "Polígono de análise desenhado sobre a imagem e uso da AOI habilitado."})

            with page.expect_response(lambda response: response.request.method == "POST" and
                                      response.url.endswith("/api/tools/classify"), timeout=240_000) as pending:
                form.get_by_role("button", name="Gerar Grupos").click()
            response = pending.value
            assert response.status == 200, {"status": response.status, "body": response.text()[:500]}
            result = response.json()
            assert result["n_clusters"] == 5, result
            clusters = result["clusters"]
            assert len(clusters) == 5 and all(item["pixel_count"] > 0 for item in clusters), clusters
            assert result["analise"] and result["analise"].get("id"), result
            analysis_id = int(result["analise"]["id"])
            record["analysis"] = {
                "id": analysis_id,
                "output_path": result["output_path"],
                "cluster_count": len(clusters),
                "total_valid_pixels": result["total_valid_pixels"],
                "sample_pixels": result["sample_pixels"],
                "pixel_area_m2": result["pixel_area_m2"],
                "valid_area_m2": result["valid_area_m2"],
                "clusters": clusters,
                "aoi_pixel_count": result["total_valid_pixels"],
            }
            assert classify_request.get("ortomapa_id") == ORTHO_ID
            assert classify_request.get("projeto_id") == PROJECT_ID
            assert classify_request.get("n_clusters") == 5
            assert classify_request.get("aoi", {}).get("type") == "Polygon", classify_request
            record["request"] = {"ortomapa_id": classify_request["ortomapa_id"],
                                  "projeto_id": classify_request["projeto_id"],
                                  "algorithm": classify_request["algorithm"],
                                  "n_clusters": classify_request["n_clusters"],
                                  "aoi_type": classify_request["aoi"]["type"],
                                  "aoi_vertices": len(classify_request["aoi"]["coordinates"][0])}
            form.locator(".result-stats.class-result").wait_for()
            assert form.locator(".cluster-row").count() == 5
            assert form.get_by_text("KMeans RGB sem rotulos semanticos.", exact=True).is_visible()
            page.wait_for_function(
                f"() => Array.from(document.querySelectorAll('.leaflet-tile-loaded')).some(e => e.src.includes('/api/analises/{analysis_id}/tile/'))",
                timeout=60_000)
            page.wait_for_timeout(3000)
            output_tiles = page.locator(".leaflet-tile-loaded").evaluate_all(
                f"els => els.map(el => el.src).filter(src => src.includes('/api/analises/{analysis_id}/tile/'))")
            record["output_map_tiles_loaded"] = len(output_tiles)
            sampled_tiles = []
            for tile_src in output_tiles[:24]:
                path = urlparse(tile_src).path
                coordinates = path.split("/tile/", 1)[1].removesuffix(".png").split("/")
                tile_response = page.request.get(API + path,
                                                 headers={"Authorization": f"Bearer {token}"})
                assert tile_response.status == 200, tile_response.status
                tile = Image.open(__import__("io").BytesIO(tile_response.body())).convert("RGBA")
                opaque = int((np.asarray(tile.getchannel("A")) > 0).sum())
                sampled_tiles.append({"zxy": [int(value) for value in coordinates],
                                      "http_status": tile_response.status,
                                      "size": list(tile.size), "opaque_pixels": opaque})
                if opaque and "sample_tile" not in record:
                    record["sample_tile"] = sampled_tiles[-1]
                    tile.save(OUT / "07_tile_kmeans_classificacao.png")
            record["output_tile_samples"] = sampled_tiles
            if "sample_tile" not in record:
                raise AssertionError({"output_map_tiles_loaded": len(output_tiles),
                                      "sampled_tiles": sampled_tiles})
            assert record["sample_tile"]["size"] == [256, 256]
            shot = "06_ui_resultado_kmeans_grupos_e_mapa.png"
            page.screenshot(path=str(OUT / shot), full_page=True, animations="disabled")
            record["screenshots"].append({"file": shot,
                "meaning": "Raster de grupos exibido no mapa, cinco estatísticas e aviso semântico visíveis."})

            with get_connection() as conn:
                cur = conn.cursor(dictionary=True)
                cur.execute("SELECT status,resultado_path,resultado_json FROM analises WHERE id=%s",
                            (analysis_id,))
                saved = cur.fetchone()
            assert saved and saved["status"] == "concluida" and Path(saved["resultado_path"]).is_file()
            record["persistence"] = {"status": saved["status"],
                                     "result_file_bytes": Path(saved["resultado_path"]).stat().st_size}
            record["browser_errors_free"] = not record["browser_errors"] and not record["console_errors"]
            record["result"] = "PASS_FUNCTIONAL_UI_AND_REAL_DATA"
            browser.close()
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=15)
        for stream in logs:
            stream.close()
    (OUT / "playwright_manifest.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"result": record["result"], "analysis": record["analysis"]["id"],
                      "groups": record["analysis"]["cluster_count"],
                      "valid_pixels": record["analysis"]["total_valid_pixels"],
                      "tiles": record["output_map_tiles_loaded"], "screenshots": record["screenshots"]},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
