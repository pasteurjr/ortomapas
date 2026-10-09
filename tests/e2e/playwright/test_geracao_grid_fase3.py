"""Validacao visual da geracao de grid fotogrametrica (Fase 3)."""

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
OUTPUT = Path(os.getenv("SCREENSHOTS_DIR", str(ROOT / "runtime/screenshots/geracao_grid_fase3"))) / RUN_ID
OUTPUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    result = {"suite": "geracao_grid_fase3", "base_url": BASE_URL, "steps": []}
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
            result["steps"].append({"id": "F3-UI-001", "status": "passed", "description": "Editor de missao aberto", "screenshot": shot("01_editor")})

            page.get_by_label("Nome da missao").fill("Demo Grid Fotogrametrico - Fase 3")
            map_box = page.locator(".planner-map").bounding_box()
            if not map_box:
                raise AssertionError("Mapa nao encontrado")
            x, y, width, height = map_box["x"], map_box["y"], map_box["width"], map_box["height"]

            def click_map(rx: float, ry: float) -> None:
                page.mouse.click(x + width * rx, y + height * ry)
                page.wait_for_timeout(150)

            page.get_by_role("button", name="Desenhar area de interesse").click()
            points = [(0.25, 0.30), (0.58, 0.30), (0.58, 0.58), (0.25, 0.58)]
            for point in points:
                click_map(*point)
            click_map(*points[0])
            page.get_by_text("Area de interesse definida").wait_for(timeout=5000)

            page.get_by_role("button", name="Desenhar zona de exclusao").click()
            exclusion = [(0.68, 0.65), (0.78, 0.65), (0.78, 0.75), (0.68, 0.75)]
            for point in exclusion:
                click_map(*point)
            click_map(*exclusion[0])
            page.get_by_text("Zona de exclusao adicionada").wait_for(timeout=5000)

            page.get_by_role("button", name="Marcar ponto de decolagem").click()
            click_map(0.28, 0.66)
            page.get_by_role("tooltip", name="Takeoff").wait_for(timeout=5000)
            page.get_by_role("button", name="Salvar missao").click()
            page.get_by_text("Missao salva no projeto").wait_for(timeout=10000)
            result["steps"].append({"id": "F3-UI-002", "status": "passed", "description": "AOI, exclusao e takeoff persistidos", "screenshot": shot("02_geometrias")})

            page.locator('label').filter(has_text="Espacamento linhas").locator('input').fill("150")
            page.locator('label').filter(has_text="Espacamento fotos").locator('input').fill("150")
            grid_button = page.get_by_role("button", name="Gerar grid fotogrametrica")
            grid_button.click()
            page.wait_for_timeout(500)
            page.get_by_text("Grid gerado:").wait_for(timeout=30000)
            page.locator(".grid-summary").wait_for(timeout=10000)
            result["steps"].append({"id": "F3-UI-003", "status": "passed", "description": "Grid, pontos de captura e resumo calculados", "screenshot": shot("03_grid_gerada")})

            if page.locator(".waypoint-marker").count() < 2:
                raise AssertionError("A rota nao exibiu pontos de captura")
            result["steps"].append({"id": "F3-UI-004", "status": "passed", "description": "Rota visual exibida no mapa", "screenshot": shot("04_rota_visual")})
        except Exception as exc:
            result["steps"].append({"id": "F3-UI-ERROR", "status": "failed", "description": "Fluxo visual da Fase 3", "error": str(exc), "screenshot": shot("99_erro")})
        finally:
            context.close()
            browser.close()

    result["status"] = "passed" if all(step["status"] == "passed" for step in result["steps"]) else "failed"
    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    (OUTPUT / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Validacao Playwright - Fase 3", "", f"**Status:** `{result['status']}`", "", "| ID | Status | Evidencia |", "|---|---|---|"]
    for step in result["steps"]:
        lines.append(f"| {step['id']} | {step['status']} | `{step.get('screenshot', '-')}` |")
    (OUTPUT / "relatorio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(OUTPUT)}, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
