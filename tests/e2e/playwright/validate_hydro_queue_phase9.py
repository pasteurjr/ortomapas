"""Validacao visual autenticada da fila hidrologica sobre o DTM persistido do projeto ODM."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-09/playwright"
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176").rstrip("/")
API = os.getenv("API_URL", "http://127.0.0.1:8888").rstrip("/")
EMAIL = os.getenv("E2E_EMAIL", "")
PASSWORD = os.getenv("E2E_PASSWORD", "")
PROJECT_ID = int(os.getenv("UC020_PROJECT_ID", "88"))
DTM_ID = int(os.getenv("UC020_DTM_ID", "72"))
OPERATIONS = [
    ("flow_direction", "Direcao de fluxo D8", "01_direcao_fluxo"),
    ("flow_accumulation", "Acumulacao de fluxo D8", "02_acumulacao_fluxo"),
    ("twi", "Indice topografico de umidade (TWI)", "03_twi"),
]


def save(page, name, description, manifest):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True, animations="disabled")
    manifest["screenshots"].append({"file": path.name, "description": description})


def authenticated_json(page, method, path, data=None):
    token = page.evaluate("localStorage.getItem('ortomapas_token')")
    response = getattr(page.request, method.lower())(
        f"{API}{path}",
        data=data,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30_000,
    )
    payload = response.json() if response.ok else {"detail": response.text()}
    return response, payload


def compact_result(result):
    """Keep evidence useful without copying per-bin histograms or local paths."""
    if not isinstance(result, dict):
        return result
    stats = result.get("stats") or {}
    keep_stats = {
        key: stats[key]
        for key in ("valid_cells", "total_pixels", "valid_pixels", "minimum_cells", "maximum_cells",
                    "min", "max", "mean", "median", "std", "direction_codes", "working_grid")
        if key in stats
    }
    provenance = result.get("provenance") or {}
    keep_provenance = {
        key: provenance[key]
        for key in ("algorithm", "source_type", "source_ortomapa_id", "parameters", "working_grid")
        if key in provenance
    }
    return {
        key: result[key]
        for key in ("crs", "width", "height", "bbox_sul", "bbox_oeste", "bbox_norte", "bbox_leste", "style")
        if key in result
    } | {"stats": keep_stats, "provenance": keep_provenance}


def main():
    if not EMAIL or not PASSWORD:
        raise RuntimeError("Defina E2E_EMAIL e E2E_PASSWORD para a conta proprietária do projeto.")
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {
        "started_at": datetime.now().astimezone().isoformat(),
        "project_id": PROJECT_ID,
        "source_dtm_id": DTM_ID,
        "operations": [],
        "screenshots": [],
        "page_errors": [],
        "llm_calls": 0,
        "scope": "Operacoes da fila iniciadas pela interface, sobre o DTM ODM persistido; sem chamar o copiloto/LLM.",
    }
    tile_responses = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, executable_path="/usr/bin/google-chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        page.set_default_timeout(30_000)
        page.on("pageerror", lambda error: manifest["page_errors"].append(str(error)))
        page.on("response", lambda response: tile_responses.append({"url": response.url, "status": response.status})
                if f"/api/analises/" in response.url and "/tile/" in response.url else None)

        page.goto(UI, wait_until="networkidle")
        save(page, "00_login", "Tela de login antes de autenticar no Ortomapas.", manifest)
        page.locator('input[type="email"]').fill(EMAIL)
        page.locator('input[type="password"]').fill(PASSWORD)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.locator(".workspace-sidebar-nav").wait_for()

        response, projects_payload = authenticated_json(page, "get", "/api/projetos")
        assert response.status == 200, projects_payload
        projects = projects_payload.get("projetos", projects_payload if isinstance(projects_payload, list) else [])
        project = next(item for item in projects if int(item["id"]) == PROJECT_ID)
        project_name = project["nome"]
        page.get_by_text(project_name, exact=True).first.click()
        page.wait_for_timeout(1000)

        response, assets_payload = authenticated_json(page, "get", f"/api/ortomapas?projeto_id={PROJECT_ID}")
        assert response.status == 200, assets_payload
        assets = assets_payload.get("ortomapas", assets_payload if isinstance(assets_payload, list) else [])
        dtm = next(item for item in assets if int(item["id"]) == DTM_ID)
        assert str(dtm.get("tipo", "")).lower() == "dtm", dtm
        manifest["project"] = {"name": project_name}
        manifest["source"] = {"id": DTM_ID, "type": dtm["tipo"], "name": dtm["nome"]}

        page.locator(".workspace-sidebar-nav .workspace-nav-item").filter(has_text="Análises").click()
        page.locator(".leaflet-container").wait_for()
        save(page, "00_projeto_analises", "Projeto #88 autenticado, workspace Análises e mapa disponíveis.", manifest)

        previous_layers = []
        for hydro_type, expected_name, slug in OPERATIONS:
            for previous_name in previous_layers:
                previous_layer = page.locator(".layer-item").filter(has_text=previous_name)
                if previous_layer.count():
                    previous_layer.locator(".remove-btn").click()
                    page.wait_for_timeout(250)
            page.locator('.status-btn[title="Nova Analise"]').click()
            modal = page.locator(".modal")
            modal.wait_for()
            selects = modal.locator("select")
            selects.nth(0).select_option(str(DTM_ID))
            selects.nth(1).select_option("hidrologia")
            selects.nth(2).select_option(hydro_type)
            modal.locator('input[placeholder*="NDVI Fazenda Norte"]').fill(f"Fase 9 - {expected_name}")
            queue_checkbox = modal.locator('input[type="checkbox"]')
            assert queue_checkbox.count() == 1, "Opção de fila não apareceu para esta análise"
            queue_checkbox.check()
            assert modal.get_by_text("Enviar para fila de processamento", exact=True).is_visible()
            assert modal.locator(".queue-task-group .hint").is_visible()
            save(page, f"{slug}_formulario", f"Formulário preenchido com DTM #{DTM_ID}, {expected_name} e execução enfileirada.", manifest)

            with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/api/analises")) as pending_response:
                modal.get_by_role("button", name="Criar e Executar").click()
            response = pending_response.value
            body = response.json() if response.ok else {"detail": response.text()}
            assert response.status == 202, {"status": response.status, "body": body}
            analysis_id = int(body["id"])
            task_id = int(body["tarefa_id"])
            operation_result = {"type": hydro_type, "name": expected_name, "analysis_id": analysis_id,
                                "task_id": task_id, "post_status": response.status}

            deadline = time.monotonic() + 120
            latest = None
            while time.monotonic() < deadline:
                detail_response, latest = authenticated_json(page, "get", f"/api/analises/{analysis_id}")
                assert detail_response.status == 200, latest
                if latest.get("status") in {"concluida", "erro"}:
                    break
                page.wait_for_timeout(1000)
            assert latest and latest.get("status") == "concluida", {"analysis_id": analysis_id, "result": latest}
            operation_result.update({
                "status": latest["status"],
                "result_path_present": bool(latest.get("resultado_path")),
                "result": compact_result(latest.get("resultado", {})),
            })

            page.wait_for_timeout(1500)
            refresh = page.locator('.status-btn[title="Atualizar"]')
            if refresh.count():
                refresh.click()
            result_row = page.locator(f'.result-item[data-analysis-id="{analysis_id}"]')
            result_row.wait_for(timeout=30_000)
            result_row.click()
            result_row.scroll_into_view_if_needed()
            page.wait_for_timeout(2500)
            operation_tiles = [item for item in tile_responses if f"/api/analises/{analysis_id}/tile/" in item["url"]]
            operation_result["tile_statuses"] = [item["status"] for item in operation_tiles]
            operation_result["tile_200_count"] = sum(item["status"] == 200 for item in operation_tiles)
            operation_result["map_layer_visible"] = bool(operation_tiles)
            operation_result["stats_panel_visible"] = page.get_by_text("Estatisticas", exact=True).is_visible()
            save(page, f"{slug}_resultado_mapa", f"Resultado {expected_name} concluído, selecionado e solicitado no mapa.", manifest)
            assert operation_result["result_path_present"], operation_result
            assert operation_result["map_layer_visible"] and operation_result["tile_200_count"] > 0, operation_result
            assert operation_result["stats_panel_visible"], operation_result
            manifest["operations"].append(operation_result)
            previous_layers.append(expected_name)
            (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        assert not manifest["page_errors"], manifest["page_errors"]
        manifest["finished_at"] = datetime.now().astimezone().isoformat()
        (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
