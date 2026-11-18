"""Finish one versioned ODM run and compare its real products for UC-029.

Uses the existing public Aukerman flight in project #88, reprocesses the 77
preserved photos at a coarser orthophoto resolution, imports the outputs, and
compares spatial metadata and common raster samples with processing #21.
The temporary signed auth token is never written to the manifest.
"""
from __future__ import annotations

import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path
from shutil import which

import numpy as np
import rasterio
import requests
from laspy import open as open_las
from playwright.sync_api import sync_playwright
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from backend.config import DATA_DIR
from backend.database.connection import get_connection
from backend.routers.auth import _token

API = "http://127.0.0.1:8888"
UI = "http://127.0.0.1:5176"
NODE = "http://127.0.0.1:8021"
PROJECT_ID = 88
PARENT_ID = 21
USER_ID = 60
TARGET_CM = 10
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-09/playwright/uc029_reprocess"
MANIFEST_PATH = OUT / "manifest.json"


def save_manifest(manifest: dict) -> None:
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def capture(page, manifest: dict, name: str, description: str) -> None:
    prefix = manifest.get("child_task_prefix")
    if prefix:
        row = page.locator(".task-row").filter(has_text=prefix)
        if row.count():
            row.scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True, animations="disabled")
    manifest.setdefault("screenshots", []).append({"file": f"{name}.png", "description": description})
    save_manifest(manifest)


def product_summary(path: Path) -> dict:
    with rasterio.open(path) as ds:
        return {
            "file": str(path.relative_to(ROOT)),
            "bytes": path.stat().st_size,
            "width": ds.width,
            "height": ds.height,
            "bands": ds.count,
            "crs": str(ds.crs) if ds.crs else None,
            "resolution": [abs(float(ds.res[0])), abs(float(ds.res[1]))],
            "bounds": [float(ds.bounds.left), float(ds.bounds.bottom), float(ds.bounds.right), float(ds.bounds.top)],
            "nodata": ds.nodata,
        }


def compare_raster_samples(old_path: Path, new_path: Path, band_count: int) -> dict:
    """Compare a centered 512px window on the old grid after bilinear warp."""
    with rasterio.open(old_path) as old, rasterio.open(new_path) as new:
        if old.crs != new.crs:
            raise AssertionError(f"CRS divergiu: {old.crs} != {new.crs}")
        left = max(old.bounds.left, new.bounds.left)
        bottom = max(old.bounds.bottom, new.bounds.bottom)
        right = min(old.bounds.right, new.bounds.right)
        top = min(old.bounds.top, new.bounds.top)
        if left >= right or bottom >= top:
            raise AssertionError("As versões não têm sobreposição espacial")
        overlap_area = (right - left) * (top - bottom)
        old_area = (old.bounds.right - old.bounds.left) * (old.bounds.top - old.bounds.bottom)
        overlap_ratio = overlap_area / old_area
        px, py = abs(old.res[0]), abs(old.res[1])
        col_min = max(0, math.floor((left - old.bounds.left) / px))
        col_max = min(old.width, math.ceil((right - old.bounds.left) / px))
        row_min = max(0, math.floor((old.bounds.top - top) / py))
        row_max = min(old.height, math.ceil((old.bounds.top - bottom) / py))
        width = min(512, col_max - col_min)
        height = min(512, row_max - row_min)
        if width < 32 or height < 32:
            raise AssertionError(f"Sobreposição útil muito pequena para comparar: {width}x{height}")
        col = col_min + (col_max - col_min - width) // 2
        row = row_min + (row_max - row_min - height) // 2
        window = Window(col, row, width, height)
        bands = min(band_count, old.count, new.count)
        with WarpedVRT(
            new,
            crs=old.crs,
            transform=old.transform,
            width=old.width,
            height=old.height,
            resampling=Resampling.bilinear,
        ) as aligned:
            a = old.read(list(range(1, bands + 1)), window=window).astype(np.float32)
            b = aligned.read(list(range(1, bands + 1)), window=window).astype(np.float32)
            mask = (old.dataset_mask(window=window) > 0) & (aligned.dataset_mask(window=window) > 0)
            if not np.any(mask):
                raise AssertionError("A janela comum não contém pixels válidos")
            delta = a[:, mask] - b[:, mask]
            return {
                "sample_window_old_grid_pixels": [width, height],
                "common_valid_pixels": int(mask.sum()),
                "overlap_ratio_of_old_extent": round(overlap_ratio, 6),
                "bands_compared": bands,
                "mean_absolute_difference": float(np.mean(np.abs(delta))),
                "root_mean_square_difference": float(np.sqrt(np.mean(delta ** 2))),
                "max_absolute_difference": float(np.max(np.abs(delta))),
                "note": "Comparison only; no acceptance threshold was defined for pixel values or elevations.",
            }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    node_info = requests.get(f"{NODE}/info", timeout=15).json()
    if node_info.get("taskQueueCount") != 0:
        raise RuntimeError(f"NodeODM não está ocioso; fila={node_info.get('taskQueueCount')}")

    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nome,email,perfil,ativo FROM usuarios WHERE id=%s AND ativo=TRUE", (USER_ID,))
        user = cur.fetchone()
        cur.execute("SELECT id,nome FROM projetos WHERE id=%s", (PROJECT_ID,))
        project = cur.fetchone()
        cur.execute("SELECT * FROM processamentos_odm WHERE id=%s AND projeto_id=%s", (PARENT_ID, PROJECT_ID))
        parent = cur.fetchone()
        cur.execute("SELECT count(*) AS n,coalesce(sum(tamanho_bytes),0) AS bytes FROM voo_fotos WHERE voo_id=%s", (parent["voo_id"],))
        photos = cur.fetchone()
        cur.execute("SELECT id,tipo,caminho FROM produtos_processamento WHERE processamento_id=%s ORDER BY id", (PARENT_ID,))
        parent_products = [dict(row) for row in cur.fetchall()]
        cur.execute("""SELECT COALESCE(MAX(NULLIF(parametros->'reprocessamento'->>'version','')::INTEGER),1) AS latest
            FROM processamentos_odm WHERE id=%s OR parametros->'reprocessamento'->>'root_processing_id'=%s""",
            (PARENT_ID, str(PARENT_ID)))
        expected_version = int(cur.fetchone()["latest"]) + 1
    if not user or not project or not parent or parent["status"] != "concluido" or photos["n"] != 77:
        raise RuntimeError("Projeto/processamento original concluído ou conjunto esperado de 77 fotos indisponível")
    old_by_kind = {p["tipo"]: p for p in parent_products}
    for kind in ("ortomosaico", "dsm", "dtm"):
        if kind not in old_by_kind or not (Path(DATA_DIR) / old_by_kind[kind]["caminho"]).is_file():
            raise RuntimeError(f"Raster original ausente: {kind}")
    if not (Path(DATA_DIR) / old_by_kind["relatorio"]["caminho"]).is_file():
        raise RuntimeError("Relatório original ausente")

    token = _token(user)
    manifest = {
        "started_at": datetime.now().astimezone().isoformat(),
        "case": "UC-029 / reprocessamento completo e comparação de versões",
        "project_id": PROJECT_ID,
        "parent_processing_id": PARENT_ID,
        "parent_status_before": parent["status"],
        "parent_task_uuid": parent["odm_task_id"],
        "preserved_photos": int(photos["n"]),
        "preserved_photo_bytes": int(photos["bytes"]),
        "nodeodm": {k: node_info.get(k) for k in ("version", "engine", "engineVersion", "taskQueueCount", "maxParallelTasks")},
        "requested_change": {"option": "orthophoto-resolution", "value": TARGET_CM, "unit": "cm/pixel"},
        "expected_version": expected_version,
        "started_request_http": None,
        "child_processing_id": None,
        "child_task_uuid": None,
        "screenshots": [],
        "progress_observations": [],
        "page_errors": [],
        "console_errors": [],
        "llm_calls": 0,
        "token_persisted": False,
    }
    save_manifest(manifest)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=which("google-chrome"), args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1680, "height": 1100}, accept_downloads=True)
        context.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
        page = context.new_page()
        page.set_default_timeout(60_000)
        page.on("pageerror", lambda exc: manifest["page_errors"].append(str(exc)))
        page.on("console", lambda msg: manifest["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.goto(UI, wait_until="domcontentloaded")
        page.locator(".app-layout").wait_for(timeout=60_000)
        page.locator(".project-selector").click()
        page.get_by_role("option", name=project["nome"], exact=True).click()
        page.get_by_role("button", name="Voos e ODM").click()
        parent_row = page.locator(".task-row").filter(has_text=parent["odm_task_id"][:8])
        parent_row.wait_for(timeout=60_000)
        parent_row.get_by_role("button", name="Criar nova versão").wait_for()
        capture(page, manifest, "01_versao_original", "Processamento #21 concluído e seis produtos originais disponíveis antes do reprocessamento.")
        parent_row.get_by_role("button", name="Criar nova versão").click()
        dialog = page.get_by_role("dialog", name="Reprocessar com novos parâmetros")
        dialog.wait_for()
        dialog.locator("#reprocess-ortho-resolution").fill(str(TARGET_CM))
        capture(page, manifest, "02_parametro_alterado", "Formulário real com resolução da ortofoto alterada para 10 cm/pixel e aviso de preservação do original.")

        request_headers = []
        page.on("request", lambda req: request_headers.append(req.headers.get("idempotency-key"))
                if req.method == "POST" and req.url.endswith(f"/api/odm/processamentos/{PARENT_ID}/reprocessar") else None)
        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith(f"/api/odm/processamentos/{PARENT_ID}/reprocessar"), timeout=900_000) as event:
            dialog.get_by_role("button", name="Criar nova versão").click(timeout=900_000)
        submitted = event.value
        if submitted.status != 202:
            raise RuntimeError(f"POST de reprocessamento retornou HTTP {submitted.status}: {submitted.text()[:500]}")
        created = submitted.json()
        child_id = int(created["processing_id"])
        task_uuid = created["task"]["uuid"]
        if created.get("version") != expected_version or created.get("images_count") != 77 or created.get("reprocessed_from_id") != PARENT_ID:
            raise AssertionError(f"Linhagem/versão/fotos inesperados: {created}")
        manifest.update({
            "started_request_http": submitted.status,
            "child_processing_id": child_id,
            "child_task_uuid": task_uuid,
            "child_task_prefix": task_uuid[:8],
            "version": created.get("version"),
            "source_bytes_submitted": created.get("total_bytes"),
            "effective_options": created.get("options"),
            "idempotency_key_sent": bool(request_headers and request_headers[-1]),
        })
        save_manifest(manifest)
        child_row = page.locator(".task-row").filter(has_text=task_uuid[:8])
        child_row.wait_for(timeout=60_000)
        capture(page, manifest, "03_tarefa_ativa_nodeodm", "Versão nova enviada ao NodeODM real e visível na fila; o processamento de origem continua concluído.")

        deadline = time.monotonic() + 2 * 60 * 60
        last_record = 0.0
        last_code = None
        while time.monotonic() < deadline:
            response = requests.get(f"{NODE}/task/{task_uuid}/info", timeout=30)
            if response.status_code != 200:
                raise RuntimeError(f"NodeODM retornou HTTP {response.status_code} durante acompanhamento")
            info = response.json()
            status = info.get("status") or {}
            code = status.get("code")
            progress = float(info.get("progress") or 0)
            if code != last_code or time.monotonic() - last_record >= 60:
                observation = {
                    "observed_at": datetime.now().astimezone().isoformat(),
                    "code": code,
                    "state": status.get("name") or status.get("text"),
                    "progress_percent": progress,
                }
                manifest["progress_observations"].append(observation)
                save_manifest(manifest)
                print(json.dumps({"event": "odm_progress", **observation, "processing_id": child_id}, ensure_ascii=False), flush=True)
                last_record = time.monotonic()
                last_code = code
            if code == 40:
                manifest["nodeodm_terminal"] = status
                break
            if code in {30, 50}:
                manifest["nodeodm_terminal"] = status
                save_manifest(manifest)
                raise RuntimeError(f"Reprocessamento terminou sem sucesso: {status}")
            page.wait_for_timeout(5_000)
        else:
            raise TimeoutError("Reprocessamento excedeu duas horas")

        # Refresh the application's persisted state from the real NodeODM.
        listing = requests.get(f"{API}/api/odm/processamentos", params={"projeto_id": PROJECT_ID},
                               headers={"Authorization": f"Bearer {token}"}, timeout=180)
        if listing.status_code != 200:
            raise RuntimeError(f"Listagem ODM HTTP {listing.status_code}: {listing.text[:400]}")
        state = next((j for j in listing.json().get("processamentos", []) if j["id"] == child_id), None)
        if not state or state.get("status") != "concluido":
            raise AssertionError(f"API não persistiu o estado concluído: {state}")
        child_row = page.locator(".task-row").filter(has_text=task_uuid[:8])
        page.wait_for_timeout(6_000)
        capture(page, manifest, "04_tarefa_concluida", "NodeODM informou estado concluído; a nova versão está pronta para importar, sem alterar a origem.")

        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith(f"/api/odm/processamentos/{child_id}/importar"), timeout=2 * 60 * 60 * 1000) as importing:
            child_row.get_by_role("button", name="Importar produtos", exact=True).click(timeout=2 * 60 * 60 * 1000)
        imported_response = importing.value
        if imported_response.status != 200:
            raise RuntimeError(f"Importação dos produtos retornou HTTP {imported_response.status}: {imported_response.text()[:400]}")
        imported = imported_response.json()
        manifest["import_http"] = imported_response.status
        manifest["imported_product_types"] = sorted({item["tipo"] for item in imported.get("produtos", [])})
        if not {"ortomosaico", "dsm", "dtm", "relatorio", "nuvem_pontos"}.issubset(manifest["imported_product_types"]):
            raise AssertionError(f"Produtos principais não importados: {manifest['imported_product_types']}")
        page.wait_for_timeout(2_000)
        child_row = page.locator(".task-row").filter(has_text=task_uuid[:8])
        capture(page, manifest, "05_produtos_importados", "Produtos da nova versão importados no catálogo e exibidos ao lado dos produtos da origem.")

        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id,status,engine,engine_version,parametros FROM processamentos_odm WHERE id IN (%s,%s) ORDER BY id", (PARENT_ID, child_id))
            jobs = [dict(row) for row in cur.fetchall()]
            cur.execute("SELECT id,processamento_id,tipo,caminho,crs,resolucao,largura_px,altura_px FROM produtos_processamento WHERE processamento_id IN (%s,%s) ORDER BY processamento_id,id", (PARENT_ID, child_id))
            rows = [dict(row) for row in cur.fetchall()]
            cur.execute("SELECT count(*) AS n FROM produtos_processamento WHERE processamento_id=%s", (PARENT_ID,))
            parent_count = int(cur.fetchone()["n"])
        products_by_processing = {}
        for row in rows:
            products_by_processing.setdefault(int(row["processamento_id"]), {})[row["tipo"]] = dict(row)
        old = products_by_processing[PARENT_ID]
        new = products_by_processing[child_id]
        comparisons = {}
        for kind in ("ortomosaico", "dsm", "dtm"):
            old_path = Path(DATA_DIR) / old[kind]["caminho"]
            new_path = Path(DATA_DIR) / new[kind]["caminho"]
            comparisons[kind] = {
                "original": product_summary(old_path),
                "reprocessed": product_summary(new_path),
                "sample_comparison": compare_raster_samples(old_path, new_path, 3 if kind == "ortomosaico" else 1),
            }
        with open_las(Path(DATA_DIR) / old["nuvem_pontos"]["caminho"]) as reader:
            original_points = int(reader.header.point_count)
        with open_las(Path(DATA_DIR) / new["nuvem_pontos"]["caminho"]) as reader:
            new_points = int(reader.header.point_count)
        original_ortho_res = comparisons["ortomosaico"]["original"]["resolution"][0]
        new_ortho_res = comparisons["ortomosaico"]["reprocessed"]["resolution"][0]
        if not 0.08 <= new_ortho_res <= 0.12:
            raise AssertionError(f"orthophoto-resolution=10 não resultou em pixel próximo de 0,10 m: {new_ortho_res}")
        if comparisons["ortomosaico"]["sample_comparison"]["overlap_ratio_of_old_extent"] < 0.95:
            raise AssertionError("A versão reprocessada não preservou sobreposição suficiente da extensão original")
        if parent_count != 6 or jobs[0]["status"] != "concluido" or jobs[1]["status"] != "concluido":
            raise AssertionError("A origem ou a nova versão não permaneceram concluídas com histórico/produtos")
        if jobs[1]["parametros"].get("reprocessamento", {}).get("parent_processing_id") != PARENT_ID:
            raise AssertionError("Linhagem da nova versão não persistida")

        manifest["comparison"] = {
            "parent_products_unchanged_count": parent_count,
            "parent_status": jobs[0]["status"],
            "child_status": jobs[1]["status"],
            "child_engine": jobs[1]["engine"],
            "child_engine_version": jobs[1]["engine_version"],
            "version_metadata": jobs[1]["parametros"].get("reprocessamento"),
            "original_laz_points": original_points,
            "reprocessed_laz_points": new_points,
            "original_orthophoto_pixel_m": original_ortho_res,
            "reprocessed_orthophoto_pixel_m": new_ortho_res,
            "rasters": comparisons,
            "acceptance_limit": "No independent GCP or ground truth; raster error statistics are reported for comparison only, with no scientific threshold.",
        }
        manifest["page_errors"] = list(manifest["page_errors"])
        manifest["console_errors"] = list(manifest["console_errors"])
        manifest["finished_at"] = datetime.now().astimezone().isoformat()
        if manifest["page_errors"] or manifest["console_errors"]:
            raise AssertionError(f"Erros do navegador: {manifest['page_errors']} {manifest['console_errors']}")
        save_manifest(manifest)
        browser.close()

    print(json.dumps({"result": "PASS", "processing_id": child_id, "version": created["version"],
                      "option": TARGET_CM, "original_orthophoto_pixel_m": original_ortho_res,
                      "new_orthophoto_pixel_m": new_ortho_res, "imported": manifest["imported_product_types"],
                      "page_errors": manifest["page_errors"], "console_errors": manifest["console_errors"],
                      "manifest": str(MANIFEST_PATH.relative_to(ROOT))}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
