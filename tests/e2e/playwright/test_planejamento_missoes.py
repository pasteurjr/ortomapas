"""Smoke visual da Fase 1 do planejador de missoes.

Nesta fase a interface cartografica ainda nao existe. O teste valida a
superficie publicada da API no Swagger e gera a primeira evidencia visual;
as etapas seguintes acrescentarao os passos do editor de mapas ao mesmo
roteiro.

Uso:
    BASE_URL=http://127.0.0.1:5017 python tests/e2e/playwright/test_planejamento_missoes.py
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
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5017").rstrip("/")
RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUTPUT = Path(os.getenv("SCREENSHOTS_DIR", str(ROOT / "runtime/screenshots/planejamento_missoes"))) / RUN_ID
OUTPUT.mkdir(parents=True, exist_ok=True)
FIXTURE = ROOT / "tests/fixtures/missao_captura_fase1.json"


def main() -> int:
    result = {
        "suite": "planejamento_missoes_fase1",
        "base_url": BASE_URL,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "steps": [],
    }
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    required = {"nome", "drone_perfil", "camera_perfil", "crs", "takeoff", "capture", "aoi"}
    missing = sorted(required - fixture.keys())
    result["steps"].append({
        "id": "F1-DATA-001",
        "status": "passed" if not missing else "failed",
        "description": "Fixture deterministico contem contrato minimo da missao",
        "error": f"Campos ausentes: {missing}" if missing else None,
    })
    if missing:
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        result["status"] = "failed"
        (OUTPUT / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return 1
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(OUTPUT / "video"),
        )
        page = context.new_page()
        console_errors: list[str] = []
        page.on("console", lambda message: console_errors.append(message.text) if message.type == "error" else None)

        try:
            page.goto(f"{BASE_URL}/docs", wait_until="networkidle", timeout=30000)
            tag = page.get_by_text("Missoes de captura", exact=True)
            tag.wait_for(timeout=10000)
            tag.scroll_into_view_if_needed()
            page.screenshot(path=str(OUTPUT / "01_swagger_missoes_captura.png"), full_page=False)
            result["steps"].append({
                "id": "F1-UI-001",
                "status": "passed",
                "description": "Swagger exibe a tag de missoes de captura",
                "screenshot": "01_swagger_missoes_captura.png",
            })
            if console_errors:
                raise AssertionError(f"Erros de console: {console_errors[:3]}")
        except (PlaywrightTimeoutError, PlaywrightError, AssertionError) as exc:
            page.screenshot(path=str(OUTPUT / "01_swagger_missoes_captura_error.png"), full_page=False)
            result["steps"].append({
                "id": "F1-UI-001",
                "status": "failed",
                "description": "Swagger exibe a tag de missoes de captura",
                "error": str(exc),
            })
        finally:
            context.close()
            browser.close()

    result["finished_at"] = datetime.now(timezone.utc).isoformat()
    result["status"] = "passed" if all(step["status"] == "passed" for step in result["steps"]) else "failed"
    (OUTPUT / "resultado.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Validacao Playwright - Fase 1",
        "",
        f"**Status:** `{result['status']}`  ",
        f"**Base:** `{BASE_URL}`  ",
        f"**Execucao:** `{RUN_ID}`",
        "",
        "## Resultado",
        "",
        "| ID | Status | Evidencia |",
        "|---|---|---|",
    ]
    for step in result["steps"]:
        evidence = step.get("screenshot", "-")
        lines.append(f"| {step['id']} | {step['status']} | `{evidence}` |")
    lines.extend([
        "",
        "Nesta fase o teste valida a publicacao dos endpoints no Swagger. A validacao de mapa, grid e exportacao sera acrescentada ao mesmo roteiro nas fases seguintes.",
    ])
    (OUTPUT / "relatorio.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "output": str(OUTPUT)}, ensure_ascii=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
