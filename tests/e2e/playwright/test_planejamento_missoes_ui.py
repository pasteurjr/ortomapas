"""Validacao visual do editor de missoes (Fase 2).

O roteiro usa o projeto de demonstracao criado na Fase 1. Ele e deliberadamente
deterministico para produzir telas reutilizaveis em uma futura demonstracao em
video.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
BASE_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5300").rstrip("/")
EMAIL = os.getenv("E2E_EMAIL", "phase1-1791391595@example.test")
PASSWORD = os.getenv("E2E_PASSWORD", "fase1-senha-segura")
PROJECT = os.getenv("E2E_PROJECT", "Demo Planejamento Mini 3")
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUTPUT = Path(os.getenv("SCREENSHOTS_DIR", str(ROOT / "runtime/screenshots/planejamento_missoes_ui"))) / RUN_ID
OUTPUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    result = {"suite": "planejamento_missoes_ui_fase2", "base_url": BASE_URL, "steps": []}
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(OUTPUT / "video"))
        page = context.new_page()
        console_errors: list[str] = []
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)

        def shot(name: str) -> str:
            path = OUTPUT / f"{name}.png"
            page.screenshot(path=str(path), full_page=False)
            return path.name

        try:
            page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
            # PrimeVue Password mantém o input interno sem a associação de
            # label que o get_by_label espera; use os tipos HTML estáveis.
            page.locator('input[type="email"]').fill(EMAIL)
            page.locator('input[type="password"]').fill(PASSWORD)
            page.get_by_role("button", name="Entrar").click()
            page.get_by_text("Sistema de Ortomapas", exact=True).wait_for(timeout=15000)
            result["steps"].append({"id": "F2-UI-001", "status": "passed", "description": "Login e tela principal", "screenshot": shot("01_tela_principal")})

            page.get_by_text(PROJECT, exact=True).click()
            page.get_by_role("button", name="Planejar missao").wait_for(timeout=10000)
            page.get_by_role("button", name="Planejar missao").click()
            page.get_by_role("heading", name="Missao de captura").wait_for(timeout=10000)
            result["steps"].append({"id": "F2-UI-002", "status": "passed", "description": "Editor cartografico aberto", "screenshot": shot("02_editor_aberto")})

            page.get_by_label("Nome da missao").fill("Demo Grid Mini 3 - Fase 2")
            map_box = page.locator(".planner-map").bounding_box()
            if not map_box:
                raise AssertionError("Mapa do planejador nao encontrado")
            x, y, width, height = map_box["x"], map_box["y"], map_box["width"], map_box["height"]

            def click_map(rx: float, ry: float) -> None:
                page.mouse.click(x + width * rx, y + height * ry)
                page.wait_for_timeout(180)

            # AOI: quatro vertices e fechamento no primeiro ponto.
            page.get_by_role("button", name="Desenhar area de interesse").click()
            aoi_points = [(0.25, 0.30), (0.58, 0.30), (0.58, 0.58), (0.25, 0.58)]
            for point in aoi_points:
                click_map(*point)
            # Fecha clicando novamente no primeiro vértice, como faria o usuário.
            click_map(*aoi_points[0])
            page.get_by_text("Area de interesse definida").wait_for(timeout=5000)
            result["steps"].append({"id": "F2-UI-003", "status": "passed", "description": "AOI desenhada no mapa", "screenshot": shot("03_aoi_desenhada")})

            # Exclusao e takeoff.
            page.get_by_role("button", name="Desenhar zona de exclusao").click()
            page.wait_for_timeout(500)
            # Zona de exclusão em uma área adjacente à AOI (sem cobrir o
            # painel lateral), representando obstáculo operacional.
            exclusion_points = [(0.68, 0.65), (0.78, 0.65), (0.78, 0.75), (0.68, 0.75)]
            for point in exclusion_points:
                click_map(*point)
            click_map(*exclusion_points[0])
            page.get_by_text("Zona de exclusao adicionada").wait_for(timeout=5000)
            page.get_by_role("button", name="Marcar ponto de decolagem").click()
            click_map(0.28, 0.66)
            page.get_by_role("tooltip", name="Takeoff").wait_for(timeout=5000)
            result["steps"].append({"id": "F2-UI-004", "status": "passed", "description": "Exclusao e takeoff definidos", "screenshot": shot("04_exclusao_takeoff")})

            page.get_by_label("GSD (cm/px)").fill("1.5")
            page.get_by_label("Altitude (m)").fill("50")
            page.get_by_label("Overlap frontal (%)").fill("80")
            page.get_by_label("Overlap lateral (%)").fill("70")
            result["steps"].append({"id": "F2-UI-005", "status": "passed", "description": "Parametros de captura configurados", "screenshot": shot("05_parametros_captura")})

            page.get_by_role("button", name="Adicionar waypoint").click()
            for point in [(0.27, 0.34), (0.55, 0.34), (0.55, 0.54)]:
                click_map(*point)
            page.get_by_text("3", exact=True).last.wait_for(timeout=5000)
            result["steps"].append({"id": "F2-UI-006", "status": "passed", "description": "Waypoints adicionados e rota exibida", "screenshot": shot("06_waypoints_rota")})

            page.get_by_role("button", name="Salvar missao").click()
            page.get_by_text("Missao salva no projeto").wait_for(timeout=10000)
            result["steps"].append({"id": "F2-UI-007", "status": "passed", "description": "Missao persistida no PostgreSQL", "screenshot": shot("07_missao_salva")})
            if console_errors:
                raise AssertionError(f"Erros de console: {console_errors[:3]}")
        except (PlaywrightTimeoutError, PlaywrightError, AssertionError) as exc:
            result["steps"].append({"id": "F2-UI-ERROR", "status": "failed", "description": "Fluxo visual da Fase 2", "error": str(exc), "screenshot": shot("99_erro")})
        finally:
            context.close()
            browser.close()

    result["status"] = "passed" if all(step["status"] == "passed" for step in result["steps"]) else "failed"
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    (OUTPUT / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Validacao Playwright - Fase 2", "", f"**Status:** `{result['status']}`", "", "| ID | Status | Evidencia |", "|---|---|---|"]
    for step in result["steps"]:
        lines.append(f"| {step['id']} | {step['status']} | `{step.get('screenshot', '-')}` |")
    (OUTPUT / "relatorio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(OUTPUT)}, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
