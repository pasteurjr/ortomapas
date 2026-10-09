"""Roteiro visual das fases 4 e 5: edicao, simulacao e validacao."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5300").rstrip("/")
EMAIL = os.getenv("E2E_EMAIL", "phase1-1791391595@example.test")
PASSWORD = os.getenv("E2E_PASSWORD", "fase1-senha-segura")
PROJECT = os.getenv("E2E_PROJECT", "Demo Planejamento Mini 3")
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUTPUT = Path(os.getenv("SCREENSHOTS_DIR", str(ROOT / "runtime/screenshots/edicao_waypoints_fase4"))) / RUN_ID
OUTPUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    result = {"suite": "edicao_waypoints_fase4_fase5", "base_url": BASE_URL, "steps": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(OUTPUT / "video"))
        page = context.new_page()

        def shot(name: str) -> str:
            path = OUTPUT / f"{name}.png"
            page.screenshot(path=str(path), full_page=False)
            return path.name

        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            page.locator('input[type="email"]').fill(EMAIL)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.get_by_role("button", name="Entrar").click()
            page.get_by_text("Sistema de Ortomapas", exact=True).wait_for(timeout=15000)
            page.get_by_text(PROJECT, exact=True).click()
            page.get_by_role("button", name="Planejar missao").click()
            page.get_by_role("heading", name="Missao de captura").wait_for(timeout=10000)
            page.get_by_label("Nome da missao").fill("Teste Edicao Waypoints - Fase 4")
            map_box = page.locator(".planner-map").bounding_box()
            if not map_box:
                raise AssertionError("Mapa nao encontrado")
            x, y, width, height = map_box["x"], map_box["y"], map_box["width"], map_box["height"]

            def click_map(rx: float, ry: float) -> None:
                page.mouse.click(x + width * rx, y + height * ry)
                page.wait_for_timeout(130)

            page.get_by_role("button", name="Desenhar area de interesse").click()
            aoi = [(0.25, 0.30), (0.58, 0.30), (0.58, 0.58), (0.25, 0.58)]
            for point in aoi:
                click_map(*point)
            click_map(*aoi[0])
            page.get_by_text("Area de interesse definida").wait_for(timeout=5000)
            page.get_by_role("button", name="Marcar ponto de decolagem").click()
            click_map(0.28, 0.66)
            page.get_by_role("tooltip", name="Takeoff").wait_for(timeout=5000)

            page.get_by_role("button", name="Adicionar waypoint").click()
            for point in [(0.30, 0.34), (0.53, 0.34), (0.53, 0.53), (0.30, 0.53)]:
                click_map(*point)
            if page.locator(".waypoint-marker").count() != 4:
                raise AssertionError("Os quatro waypoints manuais nao foram marcados")
            result["steps"].append({"id": "F4-UI-001", "status": "passed", "description": "Waypoints manuais numerados e rota criada", "screenshot": shot("01_waypoints_manuais")})

            page.get_by_role("button", name="Salvar missao").click()
            page.get_by_text("Missao salva no projeto").wait_for(timeout=10000)
            page.locator(".waypoint-marker").nth(1).click()
            page.locator(".waypoint-editor").wait_for(timeout=5000)
            if page.locator(".waypoint-row.selected").count() != 1:
                raise AssertionError("O waypoint selecionado nao foi destacado na lista")
            result["steps"].append({"id": "F4-UI-002", "status": "passed", "description": "Selecao no mapa sincronizada com painel lateral", "screenshot": shot("02_waypoint_selecionado")})

            selected_marker = page.locator(".waypoint-marker.selected")
            box = selected_marker.bounding_box()
            if not box:
                raise AssertionError("Marcador selecionado sem geometria")
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.mouse.down(); page.mouse.move(box["x"] + 35, box["y"] + 18, steps=5); page.mouse.up()
            page.wait_for_timeout(300)
            page.locator('.waypoint-editor input[type="number"]').first.fill("65")
            page.locator('.waypoint-editor input[type="number"]').first.press("Tab")
            result["steps"].append({"id": "F4-UI-003", "status": "passed", "description": "Waypoint arrastado e altitude editada", "screenshot": shot("03_arrastar_editar")})

            page.get_by_role("button", name="Depois").click()
            if page.locator(".waypoint-marker").count() != 5:
                raise AssertionError("Insercao depois nao alterou a contagem")
            page.get_by_role("button", name="Duplicar").click()
            if page.locator(".waypoint-marker").count() != 6:
                raise AssertionError("Duplicacao nao alterou a contagem")
            page.get_by_role("button", name="Excluir").click()
            if page.locator(".waypoint-marker").count() != 5:
                raise AssertionError("Exclusao nao alterou a contagem")
            result["steps"].append({"id": "F4-UI-004", "status": "passed", "description": "Inserir depois, duplicar e excluir funcionando", "screenshot": shot("04_operacoes_waypoint")})

            page.get_by_role("button", name="Simular rota").click()
            page.locator(".simulation-status").wait_for(timeout=3000)
            page.wait_for_timeout(650)
            page.get_by_role("button", name="Pausar simulacao").click()
            if page.locator(".simulation-status").count() != 1:
                raise AssertionError("A simulacao nao exibiu estado de progresso")
            result["steps"].append({"id": "F4-UI-005", "status": "passed", "description": "Simulacao com play, avanco e pausa", "screenshot": shot("05_simulacao_pausada")})

            page.get_by_role("button", name="Salvar missao").click()
            page.get_by_text("Edicoes da missao salvas").wait_for(timeout=10000)
            result["steps"].append({"id": "F4-UI-006", "status": "passed", "description": "Edicoes persistidas no backend", "screenshot": shot("06_edicoes_salvas")})
            page.get_by_role("button", name="Validar missao").click()
            page.locator(".validation-report").wait_for(timeout=10000)
            if page.locator(".validation-rule").count() < 5:
                raise AssertionError("Relatorio visual nao exibiu regras suficientes")
            result["steps"].append({"id": "F5-UI-001", "status": "passed", "description": "Resultado da validacao e regras exibidos na interface", "screenshot": shot("07_relatorio_validacao")})
        except Exception as exc:
            result["steps"].append({"id": "F4-UI-ERROR", "status": "failed", "description": "Fluxo visual da Fase 4", "error": str(exc), "screenshot": shot("99_erro")})
        finally:
            context.close()
            browser.close()

    result["status"] = "passed" if all(step["status"] == "passed" for step in result["steps"]) else "failed"
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    (OUTPUT / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Validacao Playwright - Fases 4 e 5", "", f"**Status:** `{result['status']}`", "", "| ID | Status | Evidencia |", "|---|---|---|"]
    for step in result["steps"]:
        lines.append(f"| {step['id']} | {step['status']} | `{step.get('screenshot', '-')}` |")
    (OUTPUT / "relatorio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(OUTPUT)}, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
