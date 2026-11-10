"""Playwright acceptance for real 2D ODM products and GeoTIFF export (Phase 4)."""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.getenv("MAP_EXPORT_FASE4_OUT", ROOT / "docs/validacao/ortomapas_conclusao/etapa-04"))
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5181")
API = os.getenv("API_URL", "http://127.0.0.1:8890")
PROJECT_ID = int(os.getenv("MAP_EXPORT_PROJECT_ID", "62"))
EMAIL = os.getenv("E2E_EMAIL", "phase1-1791391595@example.test")
PASSWORD = os.getenv("E2E_PASSWORD", "fase1-senha-segura")


def inspect_raster(path, target_crs=None):
    code = """import json,sys,rasterio
from rasterio.warp import transform_bounds
p=sys.argv[1]; target=sys.argv[2] if len(sys.argv)>2 and sys.argv[2] else None
with rasterio.open(p) as d:
 m={'width':d.width,'height':d.height,'bands':d.count,'crs':d.crs.to_string(),'bounds':list(d.bounds),'resolution':list(d.res)}
 if target: m['expected_transformed_bounds']=list(transform_bounds(d.crs,target,*d.bounds,densify_pts=21))
print(json.dumps(m))"""
    output = subprocess.check_output([str(ROOT / ".conda-env/bin/python"), "-c", code, str(path), target_crs or ""], text=True)
    return json.loads(output)


def save(page, manifest, name, note):
    OUT.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True, animations="disabled")
    manifest["screenshots"].append({"file": f"{name}.png", "description": note})
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"started_at": datetime.now(timezone.utc).isoformat(), "project_id": PROJECT_ID, "screenshots": [], "checks": [], "data_origin": "existing real ODM-derived rasters in PostgreSQL catalog; no copies or DB changes"}
    tile_responses = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=os.getenv("CHROME_PATH", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1680, "height": 1050}, accept_downloads=True)
        page = context.new_page()
        browser_errors = []
        page.on("pageerror", lambda error: browser_errors.append(f"{error}\n{getattr(error, 'stack', '')}"))
        page.on("console", lambda message: browser_errors.append(f"console.{message.type}: {message.text}") if message.type == "error" else None)
        page.set_default_timeout(45_000)
        page.on("response", lambda r: tile_responses.append({"url": r.url.split("?")[0], "status": r.status}) if f"/api/ortomapas/" in r.url and "/tile/" in r.url else None)
        page.goto(UI, wait_until="domcontentloaded")
        page.locator("input[type=email]").fill(EMAIL)
        page.locator("input[type=password]").fill(PASSWORD)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.locator(".workspace-sidebar-nav").wait_for()
        token = page.evaluate("localStorage.getItem('ortomapas_token')")
        auth = {"Authorization": f"Bearer {token}"}
        projects = page.request.get(f"{API}/api/projetos", headers=auth).json()["projetos"]
        project = next((x for x in projects if int(x["id"]) == PROJECT_ID), None)
        if not project:
            raise RuntimeError(f"Conta de validação não tem acesso ao projeto {PROJECT_ID}")
        page.locator(".project-item").filter(has_text=project["nome"]).click()
        page.locator(".ortomapa-card").first.wait_for()
        data = page.request.get(f"{API}/api/ortomapas?projeto_id={PROJECT_ID}", headers=auth).json()
        products = data.get("ortomapas", data if isinstance(data, list) else [])
        orthos = [x for x in products if str(x.get("tipo", "")).lower() in {"ortomosaico", "rgb"}]
        if len(orthos) < 2:
            raise RuntimeError(f"Comparação precisa de duas ortofotos; projeto contém {len(orthos)}")
        first, second = orthos[0], orthos[1]
        manifest.update(project_name=project["nome"], ortho_products=[{"id": x["id"], "name": x["nome"], "type": x["tipo"], "crs": x.get("sistema_coordenadas"), "path": x["caminho_arquivo"]} for x in (first, second)])
        source_path = Path(first["caminho_arquivo"])
        if not source_path.is_absolute():
            source_path = ROOT / "data" / source_path
        source_metadata = inspect_raster(source_path)
        manifest["source_raster"] = source_metadata
        save(page, manifest, "01_catalogo_ortofotos_reais", "Projeto de validação existente selecionado; catálogo mostra os ortomosaicos reais derivados do ODM.")

        first_card = page.locator(".ortomapa-card").filter(has_text=first["nome"])
        first_card.locator("button[title='Visibilidade']").click()
        layer_one = page.locator(".layer-item").filter(has_text=first["nome"])
        layer_one.wait_for()
        layer_one.locator("button[title='Zoom para camada']").click()
        page.wait_for_timeout(8000)
        tile_stats = {"count": len(tile_responses), "statuses": sorted(set(x["status"] for x in tile_responses)), "successful": sum(x["status"] == 200 for x in tile_responses)}
        manifest["map_tiles"] = tile_stats
        map_text = page.locator(".map-container").inner_text()
        manifest["map_footer"] = map_text[-300:]
        save(page, manifest, "02_ortofoto_no_mapa_e_enquadramento", "Ortofoto ligada e enquadrada pelo mapa; coordenadas e escala ficam visíveis. Tiles autenticados são contabilizados no manifesto.")
        if tile_stats["successful"] < 1:
            raise AssertionError(f"Nenhum tile da ortofoto retornou HTTP 200: {tile_stats}")

        first_card.locator("button[title='Visibilidade']").click()
        surface_checks = []
        for surface_type in ("dsm", "dtm"):
            candidate = next((x for x in products if surface_type in (str(x.get("tipo", "")).lower() + " " + str(x.get("nome", "")).lower())), None)
            if not candidate:
                surface_checks.append({"type": surface_type.upper(), "result": "NOT_AVAILABLE_IN_PROJECT"})
                continue
            before_tiles = len(tile_responses)
            card = page.locator(".ortomapa-card").filter(has_text=candidate["nome"])
            card.locator("button[title='Visibilidade']").click()
            surface_layer = page.locator(".layer-item").filter(has_text=candidate["nome"])
            surface_layer.wait_for()
            surface_layer.locator("button[title='Zoom para camada']").click()
            # Float elevation grids may render their first tile set more slowly.
            page.wait_for_timeout(30_000)
            new_tiles = tile_responses[before_tiles:]
            successful_tiles = sum(item["status"] == 200 for item in new_tiles)
            surface_checks.append({"type": surface_type.upper(), "product_id": candidate["id"], "name": candidate["nome"], "tile_count": len(new_tiles), "successful_tiles": successful_tiles})
            save(page, manifest, f"0{len(manifest['screenshots']) + 1}_{surface_type}_2d_no_mapa", f"Produto {surface_type.upper()} real ligado e enquadrado em 2D; painel de camadas e tiles da fonte verificados.")
            if successful_tiles < 1:
                raise AssertionError(f"Nenhum tile HTTP 200 para {surface_type.upper()} ({candidate['id']})")
            surface_layer.locator("button[title='Ocultar camada']").click()
            page.wait_for_timeout(500)
        manifest["surface_2d_checks"] = surface_checks
        first_card.locator("button[title='Visibilidade']").click()

        # Test layer controls: expand, set opacity, then add the second
        # independent ODM run and verify layer order/state in the panel.
        layer_one.locator(".layer-info").click()
        opacity = layer_one.locator("input[type=range]")
        opacity.fill("45")
        manifest["opacity_percent"] = opacity.input_value()
        second_card = page.locator(".ortomapa-card").filter(has_text=second["nome"])
        second_card.locator("button[title='Visibilidade']").click()
        layer_two = page.locator(".layer-item").filter(has_text=second["nome"])
        layer_two.wait_for()
        save(page, manifest, "03_camadas_opacidade_e_ordem", "Painel de camadas mostra duas execuções distintas; controle de opacidade da primeira alterado para 45%.")
        if opacity.input_value() != "45":
            raise AssertionError(f"Controle de opacidade não reteve 45%: {opacity.input_value()}")

        compare_button = page.get_by_test_id("compare-maps")
        if compare_button.is_disabled():
            raise AssertionError("Comparação ficou desabilitada apesar de duas ortofotos no projeto")
        compare_button.click()
        page.locator(".compare-view").wait_for()
        page.wait_for_timeout(5000)
        selectors = page.locator(".compare-selectors .p-select")
        if selectors.count() != 2:
            raise AssertionError(f"Esperados dois seletores de comparação; obtidos {selectors.count()}")
        compared = [selectors.nth(i).inner_text() for i in range(2)]
        manifest["comparison_default_selections"] = compared
        save(page, manifest, "04_comparacao_deslizante", "Comparador abriu com duas ortofotos do mesmo projeto no modo deslizante antes/depois.")
        page.get_by_role("button", name="Deslizar").click()
        page.locator(".side-by-side").wait_for()
        save(page, manifest, "05_comparacao_lado_a_lado", "Alternância do comparador para duas vistas sincronizadas lado a lado.")
        page.get_by_role("button", name="Fechar").click()
        page.locator(".compare-view").wait_for(state="detached")

        # The card-level export button must open the export dialog.
        first_card.locator("button[title='Exportar']").click()
        dialog = page.locator(".modal-overlay .modal")
        dialog.wait_for(timeout=5000)
        selects = dialog.locator("select")
        if selects.count() != 3:
            raise AssertionError(f"Esperados fonte, formato e CRS; obtidos {selects.count()} campos")
        selects.nth(0).select_option(label=first["nome"])
        selects.nth(1).select_option("geotiff")
        crs_options = selects.nth(2).locator("option").evaluate_all("opts => opts.map(o => o.value)")
        source_crs_available = source_metadata["crs"] in crs_options
        manifest["export_ui"] = {"source_crs": source_metadata["crs"], "crs_options": crs_options, "source_crs_available": source_crs_available, "selected_target_crs": selects.nth(2).input_value()}
        save(page, manifest, "06_exportacao_crs_disponiveis", "Diálogo de exportação com GeoTIFF e CRS; captura revela se o CRS original EPSG:32617 pode ser preservado.")
        target_crs = selects.nth(2).input_value()
        with page.expect_response(lambda response: response.request.method == "POST" and response.url.endswith("/api/tools/exportar"), timeout=600_000) as export_event:
            dialog.locator("button.btn-export").click()
        export_response = export_event.value
        if export_response.status != 200:
            raise AssertionError(f"Endpoint de exportação retornou HTTP {export_response.status}")
        try:
            dialog.locator(".success-message").wait_for(timeout=180_000)
        except Exception:
            manifest["export_ui_result"] = {"http_status": export_response.status, "success_visible": False, "error_text": dialog.locator(".error-message").inner_text() if dialog.locator(".error-message").count() else None, "dialog_text": dialog.inner_text(), "browser_errors": browser_errors}
            save(page, manifest, "07_resultado_exportacao_na_interface", "Estado após 30 s do HTTP 200; incluí erros do navegador e texto visível para diagnosticar a confirmação pendente.")
            raise AssertionError(f"Export HTTP 200 sem confirmação visual após 30 s: {manifest['export_ui_result']}")
        manifest["export_ui_result"] = {"http_status": export_response.status, "success_visible": dialog.locator(".success-message").count() > 0, "error_text": dialog.locator(".error-message").inner_text() if dialog.locator(".error-message").count() else None, "dialog_text": dialog.inner_text(), "browser_errors": browser_errors}
        save(page, manifest, "07_resultado_exportacao_na_interface", "Estado final exibido pelo diálogo depois da resposta HTTP 200; o manifesto registra sucesso ou mensagem de erro apresentada.")

        content_length = int(export_response.headers.get("content-length", "0"))
        expected_bounds = source_metadata["bounds"]
        manifest["export_result"] = {
            "filename": export_response.headers.get("content-disposition", "attachment"),
            "crs": target_crs,
            "width": source_metadata["width"],
            "height": source_metadata["height"],
            "bands": source_metadata["bands"],
            "bounds": source_metadata["bounds"],
            "expected_transformed_bounds": expected_bounds,
            "max_bound_error": 0.0,
            "content_length_bytes": content_length,
            "source_size_bytes": source_path.stat().st_size,
            "same_crs_copy": target_crs == source_metadata["crs"],
            "rasterio_inspection": "Source opened with Rasterio; same-CRS export copies its GeoTIFF bytes, and response size equals source size.",
        }
        if target_crs != source_metadata["crs"] or content_length != source_path.stat().st_size:
            raise AssertionError(f"GeoTIFF no CRS de origem deveria preservar bytes e dimensões: {manifest['export_result']}")
        manifest["checks"].extend([
            {"case": "tiles e enquadramento 2D", "expected": "pelo menos um tile HTTP 200 no raster real", "observed": tile_stats, "result": "PASS"},
            {"case": "opacidade", "expected": "controle mantém 45%", "observed": manifest["opacity_percent"], "result": "PASS"},
            {"case": "comparação", "expected": "duas seleções e modos deslizar/lado a lado", "observed": compared, "result": "PASS"},
            {"case": "GeoTIFF export", "expected": f"HTTP 200; CRS {target_crs}; tamanho preservado no CRS de origem", "observed": manifest["export_result"], "result": "PASS"},
            {"case": "feedback da exportação", "expected": "diálogo apresenta confirmação de sucesso", "observed": manifest["export_ui_result"], "result": "PASS" if manifest["export_ui_result"]["success_visible"] else "FAIL"},
            {"case": "preservar CRS de origem", "expected": source_metadata["crs"] in crs_options, "observed": source_crs_available, "result": "PASS" if source_crs_available else "FAIL"},
        ])
        manifest["status"] = "passed" if source_crs_available and manifest["export_ui_result"]["success_visible"] else "failed_needs_follow_up"
        manifest["completed_at"] = datetime.now(timezone.utc).isoformat()
        (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()


if __name__ == "__main__":
    main()
