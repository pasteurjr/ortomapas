"""Import and independently compare the already completed real NodeODM task #24."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from shutil import which

import requests
from laspy import open as open_las
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from backend.config import DATA_DIR
from backend.database.connection import get_connection
from backend.routers.auth import _token
from validate_uc029_completed_reprocess_phase9 import OUT, compare_raster_samples, product_summary, save_manifest

API = "http://127.0.0.1:8888"
UI = "http://127.0.0.1:5176"
NODE = "http://127.0.0.1:8021"
PROJECT_ID = 88
PARENT_ID = 21
CHILD_ID = 24
USER_ID = 60


def capture(page, manifest, name, description, task_prefix):
    row = page.locator(".task-row").filter(has_text=task_prefix)
    row.scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True, animations="disabled")
    manifest["screenshots"].append({"file": f"{name}.png", "description": description})
    save_manifest(manifest)


def main():
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("child_processing_id") != CHILD_ID:
        raise RuntimeError("O manifesto não identifica a tarefa #24 esperada")
    task_uuid = manifest["child_task_uuid"]
    remote = requests.get(f"{NODE}/task/{task_uuid}/info", timeout=20)
    remote.raise_for_status()
    node_info = remote.json()
    if (node_info.get("status") or {}).get("code") != 40:
        raise RuntimeError(f"NodeODM ainda não confirmou conclusão: {node_info.get('status')}")

    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nome,email,perfil,ativo FROM usuarios WHERE id=%s AND ativo=TRUE", (USER_ID,))
        user = cur.fetchone()
        cur.execute("SELECT id,nome FROM projetos WHERE id=%s", (PROJECT_ID,))
        project = cur.fetchone()
        cur.execute("SELECT id,status,engine,engine_version,parametros FROM processamentos_odm WHERE id IN (%s,%s) ORDER BY id", (PARENT_ID, CHILD_ID))
        before_jobs = [dict(row) for row in cur.fetchall()]
        cur.execute("SELECT count(*) AS n FROM produtos_processamento WHERE processamento_id=%s", (PARENT_ID,))
        parent_products_before = int(cur.fetchone()["n"])
    if not user or not project or len(before_jobs) != 2 or parent_products_before != 6:
        raise RuntimeError("Projeto/usuário ou seis produtos originais não estão disponíveis")

    token = _token(user)
    headers = {"Authorization": f"Bearer {token}"}
    listing = requests.get(f"{API}/api/odm/processamentos", params={"projeto_id": PROJECT_ID}, headers=headers, timeout=180)
    if listing.status_code != 200:
        raise RuntimeError(f"Sincronização do estado do processamento falhou: HTTP {listing.status_code}")
    child_state = next((item for item in listing.json().get("processamentos", []) if item["id"] == CHILD_ID), None)
    if not child_state or child_state.get("status") != "concluido":
        raise AssertionError(f"Estado da tarefa #24 não foi persistido como concluído: {child_state}")

    page_errors, console_errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=which("google-chrome"), args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1680, "height": 1100}, accept_downloads=True)
        context.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
        page = context.new_page()
        page.set_default_timeout(60_000)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.goto(UI, wait_until="domcontentloaded")
        page.locator(".app-layout").wait_for(timeout=60_000)
        page.locator(".project-selector").click()
        page.get_by_role("option", name=project["nome"], exact=True).click()
        page.get_by_role("button", name="Voos e ODM").click()
        row = page.locator(".task-row").filter(has_text=task_uuid[:8])
        row.wait_for(timeout=60_000)
        row.get_by_role("button", name="Importar produtos", exact=True).wait_for(timeout=60_000)
        capture(page, manifest, "06_tarefa_concluida_antes_importar", "NodeODM concluiu a versão 4; o histórico de origem permanece concluído com seis produtos.", task_uuid[:8])

        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith(f"/api/odm/processamentos/{CHILD_ID}/importar"), timeout=2 * 60 * 60 * 1000) as importing:
            row.get_by_role("button", name="Importar produtos", exact=True).click(timeout=2 * 60 * 60 * 1000)
        imported_response = importing.value
        if imported_response.status != 200:
            raise RuntimeError(f"Importação ODM HTTP {imported_response.status}: {imported_response.text()[:500]}")
        imported = imported_response.json()
        types = sorted({item["tipo"] for item in imported.get("produtos", [])})
        required = {"ortomosaico", "dsm", "dtm", "relatorio", "nuvem_pontos"}
        if not required.issubset(types):
            raise AssertionError(f"Faltam produtos esperados: {sorted(required-set(types))}")
        row = page.locator(".task-row").filter(has_text=task_uuid[:8])
        page.wait_for_timeout(2_000)
        capture(page, manifest, "07_produtos_importados_comparacao", "Ortomosaico/DSM/DTM/relatório/LAZ da versão nova importados no catálogo; produto original intacto.", task_uuid[:8])
        if page_errors or console_errors:
            raise AssertionError(f"Erros no navegador: {page_errors} {console_errors}")
        browser.close()

    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,status,engine,engine_version,parametros FROM processamentos_odm WHERE id IN (%s,%s) ORDER BY id", (PARENT_ID, CHILD_ID))
        jobs = [dict(row) for row in cur.fetchall()]
        cur.execute("SELECT count(*) AS n FROM produtos_processamento WHERE processamento_id=%s", (PARENT_ID,))
        parent_products_after = int(cur.fetchone()["n"])
        cur.execute("SELECT id,processamento_id,tipo,caminho,crs,resolucao,largura_px,altura_px FROM produtos_processamento WHERE processamento_id IN (%s,%s) ORDER BY processamento_id,id", (PARENT_ID, CHILD_ID))
        rows = [dict(row) for row in cur.fetchall()]
    by_processing = {}
    for item in rows:
        by_processing.setdefault(int(item["processamento_id"]), {})[item["tipo"]] = dict(item)
    original = by_processing[PARENT_ID]
    reprocessed = by_processing[CHILD_ID]
    rasters = {}
    for kind in ("ortomosaico", "dsm", "dtm"):
        original_path = Path(DATA_DIR) / original[kind]["caminho"]
        reprocessed_path = Path(DATA_DIR) / reprocessed[kind]["caminho"]
        rasters[kind] = {
            "original": product_summary(original_path),
            "reprocessed": product_summary(reprocessed_path),
            "sample_comparison": compare_raster_samples(original_path, reprocessed_path, 3 if kind == "ortomosaico" else 1),
        }
    with open_las(Path(DATA_DIR) / original["nuvem_pontos"]["caminho"]) as reader:
        old_points = int(reader.header.point_count)
    with open_las(Path(DATA_DIR) / reprocessed["nuvem_pontos"]["caminho"]) as reader:
        new_points = int(reader.header.point_count)

    old_resolution = rasters["ortomosaico"]["original"]["resolution"][0]
    new_resolution = rasters["ortomosaico"]["reprocessed"]["resolution"][0]
    overlap = rasters["ortomosaico"]["sample_comparison"]["overlap_ratio_of_old_extent"]
    checks = {
        "two_completed_versions": jobs[0]["status"] == "concluido" and jobs[1]["status"] == "concluido",
        "parent_product_count_unchanged": parent_products_before == parent_products_after == 6,
        "lineage_and_version": jobs[1]["parametros"].get("reprocessamento", {}).get("parent_processing_id") == PARENT_ID and jobs[1]["parametros"].get("reprocessamento", {}).get("version") == 4,
        "target_resolution_applied": 0.08 <= new_resolution <= 0.12,
        "spatial_overlap": overlap >= 0.95,
        "browser_clean": not page_errors and not console_errors,
    }
    if not all(checks.values()):
        raise AssertionError(f"Checks UC-029 não passaram: {checks}")

    manifest.update({
        "finished_at": datetime.now().astimezone().isoformat(),
        "nodeodm_terminal": node_info.get("status"),
        "import_http": imported_response.status,
        "imported_product_types": types,
        "completion": {"processing_id": CHILD_ID, "version": 4, "status": "concluido", "nodeodm_code": 40, "processing_time_ms": node_info.get("processingTime")},
        "comparison": {
            "parent_status": jobs[0]["status"], "child_status": jobs[1]["status"],
            "child_engine": jobs[1]["engine"], "child_engine_version": jobs[1]["engine_version"],
            "parent_products_before": parent_products_before, "parent_products_after": parent_products_after,
            "version_metadata": jobs[1]["parametros"].get("reprocessamento"),
            "original_laz_points": old_points, "reprocessed_laz_points": new_points,
            "original_orthophoto_pixel_m": old_resolution, "reprocessed_orthophoto_pixel_m": new_resolution,
            "rasters": rasters,
            "acceptance_limit": "Product lineage, target resolution, CRS/coverage, and output existence are checked. Pixel/elevation differences are measured without a scientific threshold or GCP/ground truth.",
        },
        "acceptance_checks": checks,
        "page_errors": page_errors, "console_errors": console_errors,
        "result": "PASS_FUNCTIONAL_UC029",
    })
    save_manifest(manifest)
    print(json.dumps({"result": manifest["result"], "processing_id": CHILD_ID, "version": 4,
                      "new_orthophoto_pixel_m": new_resolution, "overlap_ratio": overlap,
                      "imported_products": types, "checks": checks,
                      "manifest": str(manifest_path.relative_to(ROOT))}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
