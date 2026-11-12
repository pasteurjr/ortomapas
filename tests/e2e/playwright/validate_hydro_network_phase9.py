"""Playwright da rede D8 vetorial e bacia por exutorio com DTM real.

E2E_TOKEN deve ser um token de acesso valido, mantido somente no ambiente do
processo. O roteiro nao imprime nem persiste esse token.
"""
from __future__ import annotations

import json
import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-09/playwright"
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176").rstrip("/")
API = os.getenv("API_URL", "http://127.0.0.1:8888").rstrip("/")
TOKEN = os.getenv("E2E_TOKEN", "")
PROJECT_ID = int(os.getenv("UC020_PROJECT_ID", "88"))
DTM_ID = int(os.getenv("UC020_DTM_ID", "72"))


def capture(page, name, description, manifest):
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True, animations="disabled")
    manifest["screenshots"].append({"file": f"{name}.png", "description": description})


def api(page, method, path, data=None):
    response = getattr(page.request, method.lower())(
        f"{API}{path}", data=data, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30_000
    )
    payload = response.json() if response.ok else {"detail": response.text()}
    return response, payload


def wait_completed(page, analysis_id, manifest_entry):
    deadline = time.monotonic() + 180
    latest = None
    while time.monotonic() < deadline:
        response, latest = api(page, "get", f"/api/analises/{analysis_id}")
        assert response.status == 200, latest
        if latest.get("status") in {"concluida", "erro"}:
            break
        page.wait_for_timeout(1000)
    assert latest and latest.get("status") == "concluida", {"id": analysis_id, "detail": latest}
    result = latest.get("resultado") or {}
    assert latest.get("resultado_path"), latest
    stats = result.get("stats", {})
    manifest_entry.update({
        "analysis_id": analysis_id,
        "status": latest["status"],
        "output_extension": Path(latest["resultado_path"]).suffix,
        "result_path_present": True,
        "result_summary": {key: value for key, value in stats.items() if key != "output_path"},
    })
    return latest


def main():
    if not TOKEN:
        raise RuntimeError("Defina E2E_TOKEN para uma conta autorizada ao projeto de validacao.")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "started_at": datetime.now().astimezone().isoformat(),
        "project_id": PROJECT_ID,
        "source_dtm_id": DTM_ID,
        "scope": "Rede de drenagem e bacia D8 via UI/API autenticadas, sem Copiloto/LLM.",
        "authentication_note": "Token de acesso efemero assinado pelo modulo local de autenticacao para o usuario de validacao id 60; nao houve login visual nesta subetapa. O login por credenciais foi validado na 9.2.",
        "operations": [],
        "screenshots": [],
        "page_errors": [],
        "llm_calls": 0,
    }
    tile_responses = []
    analysis_posts = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/google-chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        page.set_default_timeout(30_000)
        page.on("pageerror", lambda error: manifest["page_errors"].append(str(error)))
        page.on("request", lambda request: analysis_posts.append(request.url)
                if request.method == "POST" and request.url.endswith("/api/analises") else None)
        page.on("response", lambda response: tile_responses.append({"url": response.url, "status": response.status})
                if f"/api/analises/" in response.url and "/tile/" in response.url else None)
        page.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(TOKEN) + ");")
        page.goto(UI, wait_until="networkidle")
        who_response, who = api(page, "get", "/api/auth/me")
        assert who_response.status == 200, who
        project_response, projects = api(page, "get", "/api/projetos")
        assert project_response.status == 200, projects
        projects = projects.get("projetos", projects if isinstance(projects, list) else [])
        project = next(item for item in projects if int(item["id"]) == PROJECT_ID)
        assets_response, assets = api(page, "get", f"/api/ortomapas?projeto_id={PROJECT_ID}")
        assert assets_response.status == 200, assets
        assets = assets.get("ortomapas", assets if isinstance(assets, list) else [])
        dtm = next(item for item in assets if int(item["id"]) == DTM_ID)
        assert str(dtm.get("tipo", "")).lower() == "dtm", dtm
        manifest["project"] = {"name": project["nome"]}
        manifest["source"] = {"id": DTM_ID, "type": dtm["tipo"], "name": dtm["nome"]}
        manifest["authenticated_user"] = {"id": who["id"], "profile": who["perfil"]}

        # Abrir a área de análises do projeto no mapa.
        project_match = page.get_by_text(project["nome"], exact=True).first
        if project_match.count():
            project_match.click()
        page.locator(".workspace-sidebar-nav .workspace-nav-item").filter(has_text="Análises").click()
        page.locator(".leaflet-container").wait_for()

        # 1) Rede: parâmetros métricos, produto GeoJSON e exportações GeoJSON/KML.
        page.locator('.status-btn[title="Nova Analise"]').click()
        modal = page.locator(".modal")
        modal.wait_for()
        selects = modal.locator("select")
        selects.nth(0).select_option(str(DTM_ID))
        selects.nth(1).select_option("hidrologia")
        selects.nth(2).select_option("drainage")
        modal.locator('input[placeholder*="NDVI Fazenda Norte"]').fill("Fase 9 - Rede D8 real")
        numbers = modal.locator('input[type="number"]')
        numbers.nth(0).fill("1000")
        numbers.nth(1).fill("1")
        queue = modal.locator('input[type="checkbox"]')
        assert queue.count() == 1 and modal.get_by_text("Enviar para fila de processamento", exact=True).is_visible()
        queue.check()
        capture(page, "04_drenagem_formulario", "DTM #72, rede D8, area contribuinte minima 1000 m2, ordem Strahler minima 1 e fila ativa.", manifest)
        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/api/analises")) as pending:
            modal.get_by_role("button", name="Criar e Executar").click()
        post = pending.value
        payload = post.json() if post.ok else {"detail": post.text()}
        assert post.status == 202, {"status": post.status, "body": payload}
        drainage_id = int(payload["id"])
        drainage = {"operation": "drainage", "task_id": payload["tarefa_id"], "post_status": post.status,
                    "input": {"minimum_area_m2": 1000, "minimum_strahler_order": 1}}
        drainage_data = wait_completed(page, drainage_id, drainage)
        result = drainage_data.get("resultado") or {}
        feature_collection = result.get("geojson") or {}
        features = feature_collection.get("features") or []
        assert feature_collection.get("type") == "FeatureCollection" and features, result
        assert all(f.get("geometry", {}).get("type") in {"LineString", "MultiLineString"} for f in features)
        drainage["feature_count"] = len(features)
        drainage["geometry_types"] = sorted({f["geometry"]["type"] for f in features})
        drainage["tile_statuses"] = []  # Vetor é renderizado como GeoJSON; tiles não são esperados.
        refresh = page.locator('.status-btn[title="Atualizar"]')
        if refresh.count():
            refresh.click()
            page.wait_for_timeout(1000)
        result_row = page.locator(f'.result-item[data-analysis-id="{drainage_id}"]')
        result_row.wait_for()
        result_row.click()
        page.wait_for_function("document.querySelectorAll('.leaflet-overlay-pane path').length > 0", timeout=30_000)
        page.wait_for_timeout(500)
        assert page.get_by_text("Estatisticas", exact=True).is_visible()
        vector_paths = page.locator(".leaflet-overlay-pane path").count()
        assert vector_paths >= len(features), {"expected_features": len(features), "rendered_paths": vector_paths}
        drainage["rendered_vector_path_count"] = vector_paths
        capture(page, "04_drenagem_resultado_mapa", "Rede D8 vetorial concluida, legenda/camada no mapa e estatisticas da rede.", manifest)
        for fmt in ("GeoJSON", "KML"):
            with page.expect_download() as download_info:
                page.locator(f'.layer-control-header button[title="Baixar {fmt}"]').click()
            download = download_info.value
            path = OUT / f"04_drenagem_exportada.{fmt.lower() if fmt == 'GeoJSON' else 'kml'}"
            download.save_as(path)
            content = path.read_text(encoding="utf-8")
            if fmt == "GeoJSON":
                exported = json.loads(content)
                assert exported.get("type") == "FeatureCollection" and exported.get("features")
            else:
                assert "<LineString>" in content or "<MultiGeometry>" in content
            drainage.setdefault("exports", []).append({
                "format": fmt,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
        manifest["operations"].append(drainage)

        # Limpar camada vetorial antes do fluxo de exutório para a captura ficar legível.
        remove_buttons = page.locator('.layer-control-header button[title="Remover camada"]')
        while remove_buttons.count():
            remove_buttons.first.click()
            page.wait_for_timeout(150)

        # 2) Bacia: exutório escolhido de forma visível no mapa, ajuste D8 e GeoTIFF.
        page.locator('.status-btn[title="Nova Analise"]').click()
        modal = page.locator(".modal")
        modal.wait_for()
        selects = modal.locator("select")
        selects.nth(0).select_option(str(DTM_ID))
        selects.nth(1).select_option("hidrologia")
        selects.nth(2).select_option("watershed")
        modal.locator('input[placeholder*="NDVI Fazenda Norte"]').fill("Fase 9 - Bacia D8 por exutorio")
        queue = modal.locator('input[type="checkbox"]')
        assert queue.count() == 1
        queue.check()
        posts_before_invalid_submit = len(analysis_posts)
        modal.get_by_role("button", name="Criar e Executar").click()
        validation_error = modal.locator(".error-message")
        validation_error.wait_for()
        validation_text = validation_error.inner_text()
        assert "exutório" in validation_text.lower() and len(analysis_posts) == posts_before_invalid_submit
        manifest["watershed_without_outlet"] = {"blocked": True, "error": validation_text}
        capture(page, "05_bacia_sem_exutorio_validacao", "O formulário bloqueia o envio quando não há exutório; nenhuma análise é criada.", manifest)
        modal.get_by_role("button", name="Escolher exutório no mapa").click()
        banner = page.locator(".map-interaction-banner")
        banner.wait_for()
        capture(page, "05_bacia_escolha_exutorio", "Mapa em modo de escolha; banner instrui o clique para marcar o exutorio.", manifest)
        map_box = page.locator(".leaflet-container").bounding_box()
        assert map_box
        page.mouse.click(map_box["x"] + map_box["width"] * 0.5, map_box["y"] + map_box["height"] * 0.5)
        modal.wait_for()
        assert modal.get_by_text("Ponto selecionado:").is_visible()
        # Raio pequeno e explícito: se o ponto estiver longe de célula/canal válido, o teste deve revelar.
        numbers = modal.locator('input[type="number"]')
        numbers.nth(0).fill("100")
        capture(page, "05_bacia_formulario_exutorio", "Exutorio marcado no mapa, raio de ajuste 100 m e execução por fila habilitada.", manifest)
        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/api/analises")) as pending:
            modal.get_by_role("button", name="Criar e Executar").click()
        post = pending.value
        payload = post.json() if post.ok else {"detail": post.text()}
        assert post.status == 202, {"status": post.status, "body": payload}
        watershed_id = int(payload["id"])
        watershed = {"operation": "watershed", "task_id": payload["tarefa_id"], "post_status": post.status,
                     "input": {"snap_radius_m": 100}}
        watershed_data = wait_completed(page, watershed_id, watershed)
        stats = (watershed_data.get("resultado") or {}).get("stats") or {}
        snapped = stats.get("snapped_outlet") or {}
        requested = stats.get("requested_outlet") or {}
        assert requested.get("lat") is not None and snapped.get("lat") is not None, stats
        assert 0 <= float(snapped.get("distance_m", float("inf"))) <= 100, snapped
        assert int(stats.get("watershed_cells", 0)) > 0 and float(stats.get("area_m2", 0)) > 0, stats
        watershed.update({"requested_outlet": requested, "snapped_outlet": snapped,
                          "watershed_cells": stats["watershed_cells"], "area_m2": stats["area_m2"]})
        refresh = page.locator('.status-btn[title="Atualizar"]')
        if refresh.count():
            refresh.click()
            page.wait_for_timeout(1000)
        row = page.locator(f'.result-item[data-analysis-id="{watershed_id}"]')
        row.wait_for()
        row.click()
        page.wait_for_function(
            f"Array.from(document.images).some(img => img.src.includes('/api/analises/{watershed_id}/tile/') && img.complete && img.naturalWidth > 0)",
            timeout=30_000,
        )
        page.wait_for_timeout(500)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline and not any(f"/api/analises/{watershed_id}/tile/" in x["url"] for x in tile_responses):
            page.wait_for_timeout(250)
        watershed_tiles = [x["status"] for x in tile_responses if f"/api/analises/{watershed_id}/tile/" in x["url"]]
        watershed["tile_http_200_count"] = len(watershed_tiles)
        assert watershed_tiles and all(status == 200 for status in watershed_tiles), watershed_tiles
        assert page.get_by_text("Estatisticas", exact=True).is_visible()
        assert page.locator(".leaflet-overlay-pane path").count() > 0, "Marcador do exutorio nao apareceu no mapa"
        capture(page, "05_bacia_resultado_mapa", "Bacia D8 renderizada; marcador/ajuste do exutorio e estatisticas visiveis.", manifest)
        manifest["operations"].append(watershed)
        manifest["page_errors"] = list(manifest["page_errors"])
        assert not manifest["page_errors"], manifest["page_errors"]
        manifest["finished_at"] = datetime.now().astimezone().isoformat()
        (OUT / "hydrology_network_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
