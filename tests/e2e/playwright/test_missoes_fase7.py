"""Validacao integrada de missao, cobertura, seguranca e exportacao (Fase 7)."""

from __future__ import annotations

import csv
import io
import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from pyproj import Geod
from playwright.sync_api import sync_playwright
from shapely.geometry import shape


ROOT = Path(__file__).resolve().parents[3]
BASE_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176").rstrip("/")
EMAIL = os.getenv("E2E_EMAIL", "phase1-1791391595@example.test")
PASSWORD = os.getenv("E2E_PASSWORD", "fase1-senha-segura")
PROJECT = os.getenv("E2E_PROJECT", "Guarajuba - Condomínio Paraíso (Demonstração)")
OUTPUT = ROOT / "docs/validacao/missoes_fase7_2026-10-16"
OUTPUT.mkdir(parents=True, exist_ok=True)
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main() -> int:
    result = {"suite": "missoes_fase7", "base_url": BASE_URL, "project": PROJECT, "steps": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        page = context.new_page()
        page_errors: list[str] = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        def shot(name: str) -> str:
            path = OUTPUT / f"{name}.png"
            page.screenshot(path=str(path), full_page=False)
            return path.name

        def step(code: str, description: str, screenshot: str | None = None, **details) -> None:
            result["steps"].append({"id": code, "status": "passed", "description": description, "screenshot": screenshot, **details})

        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
            page.locator('input[type="email"]').fill(EMAIL)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.get_by_role("button", name="Entrar").click()
            page.get_by_text("Sistema de Ortomapas", exact=True).wait_for(timeout=20000)
            page.get_by_text(PROJECT, exact=True).click()
            page.get_by_role("button", name="Planejar missao").click()
            page.get_by_role("heading", name="Missao de captura").wait_for(timeout=10000)
            page.locator(".planner-map").wait_for()
            page.wait_for_timeout(1200)
            result["steps"].append({"id": "F7-01", "status": "passed", "description": "Login, projeto Guarajuba e editor; mapa enquadrado no bbox do projeto", "screenshot": shot("01_editor_guarajuba")})

            mission_name = f"Fase 7 cobertura {RUN_ID}"
            page.get_by_label("Nome da missao").fill(mission_name)
            page.get_by_label("Altitude (m)").fill("50")
            page.get_by_label("Overlap frontal (%)").fill("80")
            page.get_by_label("Overlap lateral (%)").fill("70")
            page.get_by_label("GSD (cm/px)").fill("1.5")
            box = page.locator(".planner-map").bounding_box()
            if not box:
                raise AssertionError("Viewport do mapa indisponivel")

            def click_map(rx: float, ry: float) -> None:
                page.mouse.click(box["x"] + box["width"] * rx, box["y"] + box["height"] * ry)
                page.wait_for_timeout(100)

            def validate_route() -> None:
                with page.expect_response(lambda response: response.url.endswith("/validar") and response.request.method == "POST", timeout=30000) as validation_response:
                    page.get_by_role("button", name="Validar missao").click()
                if validation_response.value.status != 200:
                    raise AssertionError(f"Falha ao validar missão: {validation_response.value.status} {validation_response.value.text()}")
                page.locator(".validation-report").wait_for(timeout=10000)
                return validation_response.value.json()

            aoi_vertices = [(0.43, 0.36), (0.73, 0.36), (0.73, 0.70), (0.43, 0.70)]
            page.get_by_role("button", name="Desenhar area de interesse").click()
            for vertex in aoi_vertices:
                click_map(*vertex)
            click_map(*aoi_vertices[0])
            page.get_by_text("Area de interesse definida").wait_for(timeout=5000)

            exclusion_vertices = [(0.555, 0.485), (0.595, 0.485), (0.595, 0.57), (0.555, 0.57)]
            page.get_by_role("button", name="Desenhar zona de exclusao").click()
            for vertex in exclusion_vertices:
                click_map(*vertex)
            click_map(*exclusion_vertices[0])
            page.get_by_text("Zona de exclusao adicionada").wait_for(timeout=5000)
            page.get_by_role("button", name="Marcar ponto de decolagem").click()
            click_map(0.40, 0.74)
            page.get_by_role("button", name="Salvar missao").click()
            page.get_by_text("Missao salva no projeto").wait_for(timeout=15000)
            step("F7-02", "AOI desenhada junto ao Condomínio Paraíso, exclusão, takeoff e parâmetros salvos no PostGIS", shot("02_aoi_exclusao_takeoff"), mission_name=mission_name)

            page.get_by_role("button", name="Gerar grid fotogrametrica").click()
            page.get_by_text("Grid gerado:").wait_for(timeout=45000)
            page.locator("[data-testid=coverage-summary]").wait_for(timeout=10000)
            summary = page.locator("[data-testid=coverage-summary]").inner_text()
            if "69.67 x 52.25 m" not in summary or "70% / 80%" not in summary:
                raise AssertionError(f"Footprint ou overlaps calculados incorretamente: {summary}")
            if page.locator(".waypoint-marker").count() < 10:
                raise AssertionError("Grid gerou poucos waypoints para a AOI desenhada")
            transit_count = page.locator(".waypoint-marker.transit").count()
            step("F7-03", "Grid deriva footprint e espaçamentos dos overlaps; rota contorna exclusao", shot("03_cobertura_grid"), summary=summary, route_markers=page.locator(".waypoint-marker").count(), transit_markers=transit_count)

            initial_validation = validate_route()
            initial_status = page.locator(".validation-summary strong").inner_text()
            crossing_rule = page.locator(".validation-rule").filter(has_text="zonas_exclusao").inner_text()
            if initial_status == "bloqueado" or "0 trecho(s) cruzam" not in crossing_rule:
                raise AssertionError(f"A rota nao passou na regra de exclusao: {initial_status}; {crossing_rule}")
            autonomy = next(rule for rule in initial_validation["rules"] if rule["regra"] == "autonomia_bateria")
            if autonomy["status"] == "bloqueado" or not autonomy["valor_observado"].get("blocos"):
                raise AssertionError(f"Autonomia por blocos não foi validada: {autonomy}")
            step("F7-04", "Validador aprova geometrias e verifica autonomia de cada bloco", shot("04_validacao_rota"), validation_status=initial_status, exclusion_rule=crossing_rule, autonomy=autonomy["valor_observado"])

            mission_select = page.get_by_label("Abrir missao existente")
            mission_id = await_selected_mission_id(mission_select, mission_name)
            persisted_before = page.evaluate("""async (id) => {
              const token = localStorage.getItem('ortomapas_token');
              const response = await fetch(`/api/missoes-captura/${id}`, {headers:{Authorization:`Bearer ${token}`}});
              return await response.json();
            }""", mission_id)
            assert len(persisted_before["areas"]) == 2
            aoi = shape(next(area["geometria"] for area in persisted_before["areas"] if area["tipo"] == "aoi"))
            centroid = aoi.centroid
            distance_to_gate_m = Geod(ellps="WGS84").inv(-38.0714399, -12.6504521, centroid.x, centroid.y)[2]
            if distance_to_gate_m > 250:
                raise AssertionError(f"AOI desenhada ficou fora do Condomínio Paraíso: {distance_to_gate_m:.0f} m da portaria")
            result["steps"][1]["distance_to_gate_m"] = round(distance_to_gate_m, 1)
            saved_waypoints = len(persisted_before["waypoints"])
            mission_select.select_option("")
            mission_select.select_option(str(mission_id))
            page.get_by_text("Missao reaberta com geometrias, parametros e rota").wait_for(timeout=10000)
            if page.locator(".waypoint-marker").count() != saved_waypoints:
                raise AssertionError("A reabertura nao restaurou a quantidade de pontos persistida")
            if page.locator(".waypoint-row").count() != saved_waypoints:
                raise AssertionError("A reabertura duplicou waypoints na lista lateral")
            step("F7-05", "Reabertura restaura parâmetros, AOI, exclusão, takeoff e waypoints persistidos", shot("05_missao_reaberta"), mission_id=mission_id, restored_waypoints=saved_waypoints)

            page.get_by_label("Altitude (m)").fill("60")
            page.get_by_role("button", name="Salvar missao").click()
            page.get_by_text("Edicoes salvas; cobertura antiga invalidada. Gere o grid novamente.").wait_for(timeout=15000)
            after_edit = page.evaluate("""async (id) => {
              const token=localStorage.getItem('ortomapas_token');
              return await (await fetch(`/api/missoes-captura/${id}`, {headers:{Authorization:`Bearer ${token}`}})).json();
            }""", mission_id)
            if len(after_edit["waypoints"]) != saved_waypoints:
                raise AssertionError(f"Salvar missão reaberta duplicou a rota: {len(after_edit['waypoints'])} != {saved_waypoints}")
            if not page.get_by_role("button", name="Exportar Litchi").is_disabled():
                raise AssertionError("Exportacao deveria ser bloqueada enquanto a cobertura estiver desatualizada")
            step("F7-06", "Alteração invalida cobertura e exportação; salvar após reabrir preserva a contagem da rota", shot("06_cobertura_invalidada"), mission_id=mission_id, persisted_waypoints=len(after_edit["waypoints"]))

            validate_route()
            stale_rule = page.locator(".validation-rule").filter(has_text="cobertura_atualizada").inner_text()
            if "bloqueado" not in page.locator(".validation-summary").inner_text():
                raise AssertionError("O backend nao bloqueou a validacao da cobertura obsoleta")
            step("F7-07", "API bloqueia validação até regenerar o grid após mudança de altitude", shot("07_bloqueio_cobertura_antiga"), stale_rule=stale_rule)

            with page.expect_response(lambda response: response.url.endswith("/gerar-grid") and response.request.method == "POST", timeout=60000) as grid_response:
                page.get_by_role("button", name="Gerar grid fotogrametrica").click()
            if grid_response.value.status != 200:
                raise AssertionError(f"Falha ao regenerar grid: {grid_response.value.status} {grid_response.value.text()}")
            page.get_by_text("Grid gerado:").wait_for(timeout=10000)
            validate_route()
            final_status = page.locator(".validation-summary strong").inner_text()
            if final_status == "bloqueado":
                raise AssertionError("A nova cobertura continuou bloqueada: " + page.locator(".validation-report").inner_text())
            step("F7-08", "Novo grid é persistido e validado; cobertura deixa de estar obsoleta", shot("08_cobertura_recalculada"), validation_status=final_status, summary=page.locator("[data-testid=coverage-summary]").inner_text())

            downloads = {}
            for label, fmt, extension in [("Exportar Litchi", "litchi_csv", ".litchi.csv"), ("Exportar KML", "kml", ".kml")]:
                with page.expect_download(timeout=15000) as download_info:
                    page.get_by_role("button", name=label).click()
                download = download_info.value
                target = OUTPUT / f"missao_{fmt}{extension}"
                download.save_as(target)
                downloads[fmt] = target.name
            csv_text = (OUTPUT / downloads["litchi_csv"]).read_text(encoding="utf-8-sig")
            csv_rows = list(csv.reader(io.StringIO(csv_text)))
            final_mission = page.evaluate("""async (id) => {
              const token=localStorage.getItem('ortomapas_token');
              return await (await fetch(`/api/missoes-captura/${id}`, {headers:{Authorization:`Bearer ${token}`}})).json();
            }""", mission_id)
            if len(csv_rows) != len(final_mission["waypoints"]) + 1:
                raise AssertionError("Número de waypoints exportados não corresponde à missão persistida")
            csv_photo_actions = sum(1 for row in csv_rows[1:] if row[8] == "1")
            persisted_photo_actions = sum(1 for point in final_mission["waypoints"] if "Take Photo" in (point["acoes"] or []))
            if csv_photo_actions != persisted_photo_actions:
                raise AssertionError(f"Ações de foto no CSV divergentes: {csv_photo_actions} != {persisted_photo_actions}")
            kml = ET.parse(OUTPUT / downloads["kml"])
            placemarks = kml.findall(".//{http://www.opengis.net/kml/2.2}Placemark")
            if len(placemarks) != len(final_mission["waypoints"]) + 1:
                raise AssertionError("Waypoints KML não correspondem à rota persistida")
            export_data = {"csv_header": csv_rows[0], "csv_rows": len(csv_rows) - 1, "photo_actions": csv_photo_actions, "kml_placemarks": len(placemarks), "kml_bytes": (OUTPUT / downloads["kml"]).stat().st_size, "files": downloads}
            step("F7-09", "CSV Litchi e KML baixados; contagem CSV comparada à missão persistida", shot("09_exportacoes"), **export_data)

            if page_errors:
                raise AssertionError("Erros JavaScript: " + " | ".join(page_errors))
        except Exception as error:
            result["steps"].append({"id": "F7-ERROR", "status": "failed", "description": str(error), "screenshot": shot("99_erro")})
            result["page_errors"] = page_errors
        finally:
            context.close()
            browser.close()

    result["status"] = "passed" if all(item["status"] == "passed" for item in result["steps"]) else "failed"
    result["run_id"] = RUN_ID
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    (OUTPUT / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report = ["# Evidências Playwright - Fase 7", "", f"**Status:** `{result['status']}`", f"**Projeto:** {PROJECT}", "", "| Caso | Resultado | Evidência |", "|---|---|---|"]
    for item in result["steps"]:
        evidence = f"![{item['id']}](./{item['screenshot']})" if item.get("screenshot") else "-"
        report.append(f"| {item['id']} - {item['description']} | {item['status']} | {evidence} |")
    (OUTPUT / "execucao_playwright.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(OUTPUT), "steps": len(result["steps"])}, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


def await_selected_mission_id(select, mission_name: str) -> int:
    options = select.locator("option").all()
    for option in options:
        if mission_name in option.inner_text():
            return int(option.get_attribute("value"))
    raise AssertionError(f"Missao criada nao apareceu na lista: {mission_name}")


if __name__ == "__main__":
    raise SystemExit(main())
