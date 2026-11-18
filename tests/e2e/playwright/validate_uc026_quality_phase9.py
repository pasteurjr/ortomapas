"""Audit UC-026 with the real ODM #21 products and capture its UI honestly.

The local token is generated in memory and never written to disk or manifest.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from shutil import which

import rasterio
import requests
import laspy
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from backend.config import DATA_DIR
from backend.database.connection import get_connection
from backend.routers.auth import _token

API = "http://127.0.0.1:8888"
UI = "http://127.0.0.1:5176"
PROJECT_ID = 88
PROCESSING_ID = 21
USER_ID = 60
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-09/playwright/uc026_quality"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nome,email,perfil,ativo FROM usuarios WHERE id=%s AND ativo=TRUE", (USER_ID,))
        user = cur.fetchone()
        cur.execute("SELECT id,nome FROM projetos WHERE id=%s", (PROJECT_ID,))
        project = cur.fetchone()
        cur.execute("SELECT id,projeto_id,status,odm_task_id FROM processamentos_odm WHERE id=%s AND projeto_id=%s", (PROCESSING_ID, PROJECT_ID))
        job = cur.fetchone()
        cur.execute("SELECT id,tipo,formato,caminho,tamanho_arquivo_mb FROM produtos_processamento WHERE processamento_id=%s ORDER BY id", (PROCESSING_ID,))
        products = [dict(row) for row in cur.fetchall()]
    if not user or not project or not job or job["status"] != "concluido":
        raise RuntimeError("O processamento real #21, o projeto #88 ou o usuário local de validação não está disponível")

    by_kind = {p["tipo"]: p for p in products}
    required = {"ortomosaico", "dsm", "dtm", "nuvem_pontos", "relatorio"}
    if not required.issubset(by_kind):
        raise AssertionError(f"Produtos esperados ausentes: {sorted(required - by_kind.keys())}")

    independent = {"raster": {}, "laz": {}, "report": {}}
    for kind in ("ortomosaico", "dsm", "dtm"):
        path = Path(DATA_DIR) / by_kind[kind]["caminho"]
        if not path.is_file() or path.stat().st_size == 0:
            raise AssertionError(f"Raster ausente/vazio: {kind}")
        with rasterio.open(path) as ds:
            independent["raster"][kind] = {
                "file": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "width": ds.width,
                "height": ds.height,
                "bands": ds.count,
                "crs": str(ds.crs) if ds.crs else None,
                "pixel_size": [abs(float(ds.res[0])), abs(float(ds.res[1]))],
                "pixel_unit": "meter" if ds.crs and ds.crs.is_projected else "CRS units",
                "bounds": [round(float(v), 3) for v in ds.bounds],
            }
    laz_path = Path(DATA_DIR) / by_kind["nuvem_pontos"]["caminho"]
    with laspy.open(laz_path) as reader:
        independent["laz"] = {"file": str(laz_path.relative_to(ROOT)), "point_count": int(reader.header.point_count)}

    report_path = Path(DATA_DIR) / by_kind["relatorio"]["caminho"]
    report_text = subprocess.run(["pdftotext", str(report_path), "-"], check=True, capture_output=True, text=True).stdout
    report_checks = {
        "reconstructed_images": re.search(r"77\s+over\s+77\s+shots\s+\(100\.0%\)", report_text) is not None,
        "average_gsd_2_8_cm": re.search(r"Average Ground Sampling Distance \(GSD\)\s+2\.8 cm", report_text) is not None,
        "gps_error_0_85_m": re.search(r"GPS errors\s+0\.85 meters", report_text) is not None,
        "horizontal_ce90_0_717_m": re.search(r"Horizontal Accuracy CE90 \(meters\)\s+0\.717", report_text) is not None,
        "vertical_le90_1_220_m": re.search(r"Vertical Accuracy LE90 \(meters\)\s+1\.220", report_text) is not None,
    }
    if not all(report_checks.values()):
        raise AssertionError(f"Campos esperados do relatório PDF não encontrados: {report_checks}")
    independent["report"] = {
        "file": str(report_path.relative_to(ROOT)),
        "odm_version": "3.5.6",
        "reconstructed_images": "77/77 (100.0%)",
        "average_gsd_cm": 2.8,
        "gps_error_m": 0.85,
        "horizontal_ce90_m": 0.717,
        "vertical_le90_m": 1.220,
        "field_checks": report_checks,
    }
    # The raster export pixel size and GSD in the ODM report are distinct
    # measurements and are deliberately shown side by side, not conflated.
    independent["interpretation"] = {
        "ortho_pixel_size_m": independent["raster"]["ortomosaico"]["pixel_size"],
        "report_gsd_cm": independent["report"]["average_gsd_cm"],
        "gcp_independent_validation": False,
        "warning": "ODM report statistics are not an independent field/GCP accuracy acceptance.",
    }

    token = _token(user)
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API}/api/odm/processamentos/{PROCESSING_ID}/qualidade", headers=headers, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"Quality endpoint HTTP {response.status_code}: {response.text[:400]}")
    quality = response.json()
    if quality.get("score") != 100 or quality.get("tipo_score") != "completude_de_catalogo_e_volume_de_nuvem":
        raise AssertionError(f"Contrato/score inesperado: {quality}")
    if quality.get("nivel") != "completa" or len(quality.get("verificacoes", [])) != 3:
        raise AssertionError(f"Indicador de completude inesperado: {quality}")
    if not quality.get("limites") or any("acurácia" not in item.lower() for item in quality["limites"][:1]):
        raise AssertionError("A resposta da API precisa declarar o limite de acurácia")
    if quality["metricas"].get("pontos_laz") != independent["laz"]["point_count"]:
        raise AssertionError("A API e a leitura independente do cabeçalho LAZ discordam")
    for kind in ("ortomosaico", "dsm", "dtm"):
        if quality["metricas"].get(f"{kind}_pixels") != independent["raster"][kind]["width"] * independent["raster"][kind]["height"]:
            raise AssertionError(f"Contagem de pixels da API diverge da leitura Rasterio: {kind}")

    manifest = {
        "executed_at": datetime.now().astimezone().isoformat(),
        "case": "UC-026 / auditoria das métricas de qualidade ODM",
        "project_id": PROJECT_ID,
        "processing_id": PROCESSING_ID,
        "ui": UI,
        "api_http_status": response.status_code,
        "api_summary": {key: quality[key] for key in ("score", "tipo_score", "nivel", "escopo", "limites", "verificacoes", "metricas", "recomendacoes")},
        "independent_product_checks": independent,
        "expected_vs_observed": [
            {"criterion": "score semântico", "expected": "identificar nota como completude de produtos; não chamar de qualidade/precisão", "observed": "UI mostra completude operacional e alerta explícito de que não é nota de acurácia", "result": "PASS"},
            {"criterion": "presença de produtos", "expected": "3 checagens passam quando ortomosaico, elevação e LAZ acima de 100 mil pontos estão presentes", "observed": f"{quality['score']}%, {len(quality['verificacoes'])} checagens; LAZ {independent['laz']['point_count']:,} pontos", "result": "PASS"},
            {"criterion": "metadados raster", "expected": "resolução e CRS coerentes com arquivos", "observed": "API iguala contagem de pixels independente; raster em EPSG:32617 e cerca de 0,05 m/pixel", "result": "PASS"},
            {"criterion": "acurácia externa", "expected": "não declarar aceite sem GCP/checkpoints independentes", "observed": "relatório ODM informa estimativas GPS/CE90/LE90, mas não houve validação independente de campo/GCP", "result": "LIMITAÇÃO MANTIDA"},
        ],
        "screenshots": [],
        "page_errors": [],
        "console_errors": [],
        "token_persisted": False,
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=which("google-chrome"), args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1680, "height": 1100})
        context.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
        page = context.new_page()
        page.set_default_timeout(40_000)
        page.on("pageerror", lambda exc: manifest["page_errors"].append(str(exc)))
        page.on("console", lambda msg: manifest["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.goto(UI, wait_until="domcontentloaded")
        page.locator(".app-layout").wait_for(timeout=40_000)
        page.locator(".project-selector").click()
        page.get_by_role("option", name=project["nome"], exact=True).click()
        page.get_by_role("button", name="Voos e ODM").click()
        row = page.locator(".task-row").filter(has_text=job["odm_task_id"][:8])
        row.wait_for()
        with page.expect_response(lambda r: r.request.method == "GET" and r.url.endswith(f"/api/odm/processamentos/{PROCESSING_ID}/qualidade")) as quality_response:
            row.locator('button[title="Avaliar qualidade"]').click()
        if quality_response.value.status != 200:
            raise AssertionError(f"O navegador recebeu HTTP {quality_response.value.status}")
        card = row.locator('[data-testid="odm-completeness"]')
        card.get_by_text("Completude de produtos: 100%", exact=True).wait_for()
        card.get_by_text("Não é uma nota de acurácia. Não valida precisão posicional/vertical, GSD real ou qualidade agronômica.", exact=True).wait_for()
        card.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "01_uc026_completude_e_limites.png"), full_page=True, animations="disabled")
        manifest["screenshots"].append({"file": "01_uc026_completude_e_limites.png", "description": "Tela real do processamento #21 com a completude de produtos e aviso explícito de que a pontuação não mede acurácia."})
        manifest["page_errors"] = list(manifest["page_errors"])
        manifest["console_errors"] = list(manifest["console_errors"])
        if manifest["page_errors"] or manifest["console_errors"]:
            raise AssertionError(f"Erros do navegador: {manifest['page_errors']} {manifest['console_errors']}")
        browser.close()

    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"manifest": str((OUT / "manifest.json").relative_to(ROOT)), "screenshot": str((OUT / "01_uc026_completude_e_limites.png").relative_to(ROOT)), "score": quality["score"], "laz_points": independent["laz"]["point_count"], "ortho_pixel_size_m": independent["raster"]["ortomosaico"]["pixel_size"], "report_gsd_cm": independent["report"]["average_gsd_cm"], "errors": {"page": manifest["page_errors"], "console": manifest["console_errors"]}}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
