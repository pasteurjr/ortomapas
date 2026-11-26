#!/usr/bin/env python3
"""Playwright UI check for sidebar navigation and header notifications.

All /api responses are browser-local fixtures. No backend, model provider, or
database is called and the script performs no persistent application writes.
"""
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent
BASE_URL = os.environ.get("ORTOMAPAS_URL", "http://127.0.0.1:5176")
PENDING = {
    "id": 901,
    "nome": "Fila de validação visual",
    "tipo_analise": "declividade",
    "status": "processando",
    "criado_em": "2026-11-26T12:00:00Z",
}
PROJECT = {
    "id": 88,
    "nome": "Projeto de teste UI",
    "descricao": "Fixture apenas para conferir navegação",
    "area_estudo": "Dados simulados no navegador",
    "status": "ativo",
    "pode_editar": True,
    "bbox_norte": -12.0,
    "bbox_sul": -12.1,
    "bbox_leste": -38.0,
    "bbox_oeste": -38.1,
}


def json_response(route, data):
    route.fulfill(status=200, content_type="application/json", body=json.dumps(data))


def click_subitem(page, label):
    buttons = page.locator(".workspace-subnav button")
    labels = buttons.all_inner_texts()
    target = buttons.filter(has_text=label)
    if target.count() != 1:
        raise AssertionError("Subitem ausente/duplicado: " + label + "; visíveis=" + repr(labels))
    target.click()


def wait_for_map_tiles(page, selector, minimum=12):
    """Require visible, decoded OSM tiles before taking a map screenshot."""
    page.wait_for_function(
        """({selector, minimum}) => {
          const map = document.querySelector(selector);
          const tiles = [...(map?.querySelectorAll('.leaflet-tile') || [])];
          return tiles.length >= minimum && tiles.filter(tile => tile.complete && tile.naturalWidth > 0).length >= minimum;
        }""",
        {"selector": selector, "minimum": minimum},
        timeout=20000,
    )
    return page.locator(selector).locator(".leaflet-tile").evaluate_all(
        "tiles => ({total: tiles.length, loaded: tiles.filter(tile => tile.complete && tile.naturalWidth > 0).length})"
    )


def mock_api(route):
    request = route.request
    path = request.url.split("/api", 1)[-1].split("?", 1)[0]
    method = request.method
    if path == "/auth/me":
        json_response(route, {"id": 60, "email": "ui-fixture@example.invalid", "nome": "Teste UI", "perfil": "admin", "ativo": True})
    elif path == "/projetos" and method == "GET":
        json_response(route, {"total": 1, "projetos": [PROJECT]})
    elif path == "/projetos/88":
        json_response(route, PROJECT)
    elif path == "/ortomapas":
        json_response(route, {"total": 0, "ortomapas": []})
    elif path == "/odm/produtos":
        # A clear, expected empty state: this navigation fixture contains no DSM/DTM.
        json_response(route, {"total": 0, "produtos": []})
    elif path == "/analises":
        json_response(route, {"total": 1, "analises": [PENDING]})
    elif path == "/anotacoes":
        json_response(route, {"total": 0, "anotacoes": []})
    elif path == "/voos":
        json_response(route, {"total": 0, "voos": []})
    elif path == "/missoes-captura":
        json_response(route, {"total": 0, "missoes": []})
    elif path == "/copilot/threads" and method == "GET":
        json_response(route, {"conversas": []})
    elif path == "/copilot/threads" and method == "POST":
        json_response(route, {"id": 9901, "titulo": "Conversa de fixture"})
    elif path == "/copilot/threads/9901":
        json_response(route, {"id": 9901, "mensagens": []})
    elif path == "/agents/layers":
        json_response(route, {"camadas": []})
    elif path == "/copilot/memories":
        json_response(route, {"memorias": []})
    else:
        json_response(route, {})


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    results = {"base_url": BASE_URL, "api_mode": "browser fixtures only; no database writes", "checks": [], "screenshots": []}
    console_errors = []
    failed_requests = []
    server = None
    try:
        try:
            urllib.request.urlopen(BASE_URL, timeout=1).close()
        except Exception:
            server = subprocess.Popen(
                ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", "5176"],
                cwd=Path(__file__).resolve().parents[4] / "frontend",
                stdout=open("/tmp/ortomapas-stage1-vite.log", "w"),
                stderr=subprocess.STDOUT,
            )
            for _ in range(40):
                try:
                    urllib.request.urlopen(BASE_URL, timeout=1).close()
                    break
                except Exception:
                    if server.poll() is not None:
                        raise RuntimeError("Vite encerrou antes de ficar disponível")
                    time.sleep(0.25)
            else:
                raise RuntimeError("Vite não respondeu em 10 segundos")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1600, "height": 1000}, device_scale_factor=1)
            context.add_init_script("localStorage.setItem('ortomapas_token', 'playwright-ui-fixture-token')")
            page = context.new_page()
            page.set_default_timeout(8000)
            page.on("pageerror", lambda error: console_errors.append(str(error)))
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("requestfailed", lambda request: failed_requests.append({"url": request.url, "error": request.failure}) if request.failure != "net::ERR_ABORTED" else None)
            page.route(BASE_URL.rstrip("/") + "/api/**", mock_api)
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=10000)
            page.locator("body").wait_for(state="attached")
            try:
                page.locator(".app-layout").wait_for(timeout=8000)
            except Exception:
                page.screenshot(path=str(ROOT / "00_debug_inicio.png"), full_page=True)
                (ROOT / "00_debug_inicio.html").write_text(page.content())
                module = page.request.get(BASE_URL + "/src/main.js")
                client_module = page.request.get(BASE_URL + "/src/api/client.js")
                component_types = {}
                for component in ["ProjectList", "OrtomapCard", "MapViewer", "ToolsPanel", "AnalysisResults", "VoosList", "DrawTools", "CopilotChat", "MeasureTools", "CompareView", "AgentStatus", "AnalysisForm", "ExportDialog", "LoginView", "OdmTasks", "MissionPlanner", "LayerPanel", "GeoTiffUpload"]:
                    response = page.request.get(BASE_URL + "/src/components/" + component + ".vue")
                    component_types[component] = {"status": response.status, "type": response.headers.get("content-type"), "body": response.text()[:500] if response.headers.get("content-type", "").startswith("application/json") else ""}
                raise RuntimeError("Aplicativo não montou. URL=" + page.url + " CONSOLE=" + repr(console_errors) + " FAILED=" + repr(failed_requests) + " CLIENT=" + client_module.text()[:2200] + " MODULES=" + repr(component_types) + " MAIN=" + str(module.status))
            page.get_by_role("combobox").first.wait_for()
            page.get_by_role("combobox").first.click()
            page.get_by_role("option", name="Projeto de teste UI").click()
            page.get_by_role("button", name="Notificações: 1 análises em andamento").wait_for()
            results["main_map_tiles"] = wait_for_map_tiles(page, ".map-container", minimum=12)
            results["checks"].append({"name": "login fixture e projeto ativo", "result": "PASS"})

            # Notification button now opens meaningful state and links to its analysis row.
            page.get_by_role("button", name="Notificações: 1 análises em andamento").click()
            page.get_by_role("dialog", name="Notificações de análise").get_by_text("Fila de validação visual").wait_for()
            notification_detail = page.locator(".notification-item small").inner_text()
            assert "Processando" in notification_detail and "/" in notification_detail, notification_detail
            page.screenshot(path=str(ROOT / "01_notificacoes_abertas.png"), full_page=True)
            results["screenshots"].append("01_notificacoes_abertas.png")
            page.get_by_role("dialog", name="Notificações de análise").locator(".notification-item").click()
            page.locator("#workspace-analysis-results").wait_for()
            page.locator('[data-analysis-id="901"]').wait_for()
            results["checks"].append({"name": "sino abre análise e navega aos resultados", "result": "PASS"})

            # All rendered sidebar subitems must navigate or trigger a real action.
            page.locator(".workspace-nav-item").nth(0).click()
            click_subitem(page, "Projetos")
            page.locator("#workspace-projects").wait_for()
            click_subitem(page, "Camadas e ortomapas")
            page.locator("#workspace-layers").wait_for()
            click_subitem(page, "Perfil altimétrico")
            page.get_by_role("region", name="Perfil altimetrico").wait_for()
            page.get_by_text("Nenhum DSM / DTM disponivel").wait_for()
            page.screenshot(path=str(ROOT / "02_perfil_aberto_pelo_submenu.png"), full_page=True)
            results["screenshots"].append("02_perfil_aberto_pelo_submenu.png")
            page.locator('.elevation-profile button[title="Fechar perfil"]').click()
            click_subitem(page, "Importar dados")
            page.locator("#workspace-import").wait_for()
            page.get_by_role("button", name="Importar GeoTIFF").click()
            page.get_by_role("dialog", name="Importar GeoTIFF").wait_for()
            page.screenshot(path=str(ROOT / "03_importacao_aberta_pelo_submenu.png"), full_page=True)
            results["screenshots"].append("03_importacao_aberta_pelo_submenu.png")
            page.get_by_role("dialog", name="Importar GeoTIFF").get_by_role("button", name="Fechar", exact=True).click()
            results["checks"].append({"name": "subitens de Dados abrem seus destinos", "result": "PASS"})

            page.locator(".workspace-nav-item").nth(1).click()
            click_subitem(page, "Voos e fotos")
            page.locator("#workspace-flights").wait_for()
            click_subitem(page, "Fila e produtos ODM")
            page.locator("#workspace-odm-tasks").wait_for()
            results["checks"].append({"name": "subitens de Voos e ODM navegam aos painéis", "result": "PASS"})

            page.locator(".workspace-nav-item").nth(2).click()
            click_subitem(page, "Ferramentas espaciais")
            page.locator("#workspace-analysis-tools").wait_for()
            page.screenshot(path=str(ROOT / "04_ferramentas_analise_pelo_submenu.png"), full_page=True)
            results["screenshots"].append("04_ferramentas_analise_pelo_submenu.png")
            click_subitem(page, "Resultados")
            page.locator("#workspace-analysis-results").wait_for()
            results["checks"].append({"name": "subitens de Análises navegam às ferramentas e resultados", "result": "PASS"})

            page.locator(".workspace-nav-item").nth(3).click()
            click_subitem(page, "Planejador de captura")
            page.get_by_role("region", name="Planejador de missao de captura").wait_for()
            try:
                results["planner_tile_state"] = wait_for_map_tiles(page, ".planner-map", minimum=12)
            except Exception:
                tile_state = page.locator(".planner-map .leaflet-tile").evaluate_all(
                    "tiles => tiles.map(tile => ({complete: tile.complete, width: tile.naturalWidth, src: tile.src}))"
                )
                results["planner_tile_state"] = tile_state
                raise AssertionError("Mapa do Planejador não carregou tiles suficientes: " + repr(tile_state))
            page.wait_for_timeout(500)
            page.screenshot(path=str(ROOT / "05_planejador_aberto_pelo_submenu.png"), full_page=True)
            results["screenshots"].append("05_planejador_aberto_pelo_submenu.png")
            page.get_by_role("button", name="Fechar planejador").click()
            results["checks"].append({"name": "submenu Missões abre o planejador", "result": "PASS"})

            page.locator(".workspace-nav-item").nth(4).click()
            click_subitem(page, "Conversas do projeto")
            page.locator("#copilot-threads").wait_for()
            click_subitem(page, "Histórico e ferramentas")
            page.locator("#copilot-messages").wait_for()
            page.screenshot(path=str(ROOT / "06_copiloto_historico_pelo_submenu.png"), full_page=True)
            results["screenshots"].append("06_copiloto_historico_pelo_submenu.png")
            results["checks"].append({"name": "subitens do Copiloto levam a conversas e histórico", "result": "PASS"})

            # Gear was removed because no preferences feature exists; verify the visible inert control is gone.
            assert page.locator(".toolbar-right .pi-cog").count() == 0
            results["checks"].append({"name": "controle de configurações sem funcionalidade não é exibido", "result": "PASS"})

            # Collapsed rail remains operable and its icon buttons retain accessible names.
            page.locator(".sidebar-left .sidebar-toggle").click()
            assert page.locator(".workspace-nav-item").nth(2).get_attribute("title") == "Análises"
            page.screenshot(path=str(ROOT / "07_navegacao_recolhida.png"), full_page=True)
            results["screenshots"].append("07_navegacao_recolhida.png")
            page.keyboard.press("Tab")
            focused_nav = page.evaluate("document.activeElement?.classList?.contains('workspace-nav-item')")
            assert focused_nav, "Tab não moveu o foco para um item de navegação"
            page.keyboard.press("Enter")
            assert "active" in (page.locator(".workspace-nav-item").nth(0).get_attribute("class") or "")
            page.locator(".sidebar-left .sidebar-toggle").click()
            page.set_viewport_size({"width": 900, "height": 850})
            assert page.locator(".workspace-nav-item").first.is_visible()
            page.screenshot(path=str(ROOT / "08_viewport_compacto.png"), full_page=True)
            results["screenshots"].append("08_viewport_compacto.png")
            results["checks"].append({"name": "barra recolhida acessível por teclado e viewport compacto", "result": "PASS"})

            results["page_errors"] = console_errors
            results["failed_requests"] = failed_requests
            results["result"] = "PASS" if all(c["result"] == "PASS" for c in results["checks"]) and not console_errors and not failed_requests else "FAIL"
            browser.close()
    finally:
        if server:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
    (ROOT / "resultado.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    if results["result"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
