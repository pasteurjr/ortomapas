"""Recover an actually missing NodeODM task and finish the replacement run.

Uses the retained real Aukerman flight (project #88, processing #21): NodeODM
already reports the old UUID as missing while PostgreSQL still has all source
photos and imported products. It submits the recovery through the UI, monitors
the real NodeODM task, imports its outputs, and checks that the parent is intact.
The API/NodeODM task UUIDs are test evidence; no token or password is persisted.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from shutil import which

import requests
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from backend.config import DATA_DIR
from backend.database.connection import get_connection
from backend.routers.auth import _token
from backend.routers.odm import _nodeodm_task_missing

API = "http://127.0.0.1:8888"
UI = "http://127.0.0.1:5176"
NODE = "http://127.0.0.1:8021"
PROJECT_ID = 88
PARENT_ID = 21
USER_ID = 60
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-10/uc024_real_recovery"
POLL_SECONDS = 15
DEADLINE_SECONDS = 60 * 60
REQUIRED_PRODUCTS = {"ortomosaico", "dsm", "dtm", "relatorio", "nuvem_pontos", "modelo_3d"}


def save(manifest: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def db_snapshot():
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,nome,email,perfil,ativo FROM usuarios WHERE id=%s AND ativo=TRUE", (USER_ID,))
        user = cur.fetchone()
        cur.execute("SELECT id,nome FROM projetos WHERE id=%s", (PROJECT_ID,))
        project = cur.fetchone()
        cur.execute("SELECT * FROM processamentos_odm WHERE id=%s AND projeto_id=%s", (PARENT_ID, PROJECT_ID))
        parent = cur.fetchone()
        if not parent:
            raise RuntimeError("Processamento de origem #21 indisponível")
        cur.execute("SELECT count(*) AS n,coalesce(sum(tamanho_bytes),0) AS bytes FROM voo_fotos WHERE voo_id=%s", (parent["voo_id"],))
        photo_stats = cur.fetchone()
        cur.execute("SELECT id,tipo,caminho FROM produtos_processamento WHERE processamento_id=%s ORDER BY id", (PARENT_ID,))
        products = [dict(r) for r in cur.fetchall()]
    if not user or not project or int(photo_stats["n"]) != 77 or len(products) != 6:
        raise RuntimeError(f"Pré-condições falharam: user={bool(user)} project={bool(project)} photos={photo_stats} products={len(products)}")
    return user, project, parent, photo_stats, products


def capture(page, manifest, filename, description, task_prefix=None):
    if task_prefix:
        rows = page.locator(".task-row").filter(has_text=task_prefix)
        if rows.count():
            rows.first.scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / filename), full_page=True, animations="disabled")
    manifest.setdefault("screenshots", []).append({"file": filename, "description": description})
    save(manifest)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    user, project, parent, photos, parent_products = db_snapshot()
    token = _token(user)
    old_uuid = parent["odm_task_id"]
    node_info_before_response = requests.get(f"{NODE}/info", timeout=15)
    node_info_before_response.raise_for_status()
    node_info_before = node_info_before_response.json()
    if int(node_info_before.get("taskQueueCount", -1)) != 0:
        raise RuntimeError(f"NodeODM ocupado; fila={node_info_before.get('taskQueueCount')}")
    old_status = requests.get(f"{NODE}/task/{old_uuid}/info", timeout=15)
    if not _nodeodm_task_missing(old_status):
        raise RuntimeError(f"A tarefa #21 não está ausente no NodeODM; HTTP {old_status.status_code}")

    manifest = {
        "started_at": datetime.now().astimezone().isoformat(),
        "case": "UC-024 / recuperação real de tarefa ausente no NodeODM",
        "environment": {"project_id": PROJECT_ID, "parent_processing_id": PARENT_ID,
                        "nodeodm_version": node_info_before.get("version"),
                        "odm_engine_version": node_info_before.get("engineVersion")},
        "source": {"task_uuid": old_uuid, "task_info_http": old_status.status_code,
                   "nodeodm_missing_confirmed": True, "database_status_before": parent["status"],
                   "photo_count": int(photos["n"]), "photo_bytes": int(photos["bytes"]),
                   "preserved_product_count_before": len(parent_products),
                   "dataset": "Aukerman público já presente no projeto #88; não é voo do usuário"},
        "recovery": {}, "progress_observations": [], "screenshots": [],
        "page_errors": [], "console_errors": [], "llm_calls": 0, "token_persisted": False,
    }
    save(manifest)
    headers = {"Authorization": f"Bearer {token}"}
    listing = requests.get(f"{API}/api/odm/processamentos", params={"projeto_id": PROJECT_ID}, headers=headers, timeout=180)
    if listing.status_code != 200:
        raise RuntimeError(f"Não foi possível consultar tarefas do projeto: HTTP {listing.status_code}")
    source_state = next((j for j in listing.json().get("processamentos", []) if j["id"] == PARENT_ID), None)
    if not source_state or not source_state.get("nodeodm_missing") or not source_state.get("recovery_available"):
        raise AssertionError(f"API não marcou tarefa ausente recuperável: {source_state}")
    manifest["source"]["api_state"] = {"status": source_state.get("status"), "nodeodm_missing": True,
                                         "recovery_available": True, "stored_photos": int(photos["n"])}
    save(manifest)

    page_errors, console_errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=which("google-chrome"), args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1680, "height": 1100})
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
        parent_row = page.locator(".task-row").filter(has_text=old_uuid[:8])
        parent_row.wait_for(timeout=60_000)
        parent_row.get_by_role("button", name="Reenviar fotos preservadas", exact=True).wait_for(timeout=60_000)
        capture(page, manifest, "01_tarefa_origem_ausente.png",
                "Tarefa #21 ausente no NodeODM; fotos preservadas e controle de recuperação habilitado.", old_uuid[:8])
        parent_row.get_by_role("button", name="Reenviar fotos preservadas", exact=True).click()
        dialog = page.get_by_role("dialog", name="Reenviar fotos ao NodeODM")
        dialog.wait_for()
        capture(page, manifest, "02_confirmacao_de_recuperacao.png",
                "Confirmação informa que as fotos originais preservadas serão reenviadas e os produtos anteriores mantidos.", old_uuid[:8])
        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith(f"/api/odm/processamentos/{PARENT_ID}/recuperar"), timeout=3 * 60 * 1000) as event:
            dialog.get_by_role("button", name="Reenviar fotos", exact=True).click()
        response = event.value
        if response.status != 202:
            raise RuntimeError(f"Recuperação real falhou: HTTP {response.status} {response.text()[:700]}")
        body = response.json()
        new_id, new_uuid = int(body["processing_id"]), body["task"]["uuid"]
        if body.get("images_count") != 77 or body.get("reprocessed_from_id") != PARENT_ID:
            raise AssertionError(f"Nova tarefa não está ligada às 77 fotos/origem: {body}")
        manifest["recovery"] = {"http": response.status, "new_processing_id": new_id,
                                "new_task_uuid": new_uuid, "parent_processing_id": PARENT_ID,
                                "images_count": body["images_count"], "total_bytes": body["total_bytes"],
                                "recovery_metadata": None}
        save(manifest)
        task_row = page.locator(".task-row").filter(has_text=new_uuid[:8])
        task_row.wait_for(timeout=60_000)
        page.wait_for_timeout(1500)
        first_info = requests.get(f"{NODE}/task/{new_uuid}/info", timeout=15)
        first_info.raise_for_status()
        first_payload = first_info.json()
        if first_payload.get("status", {}).get("code") not in {10, 20, 40}:
            raise AssertionError(f"NodeODM não aceitou tarefa substituta real: {first_payload}")
        capture(page, manifest, "03_nova_tarefa_nodeodm.png",
                "Tarefa substituta criada no NodeODM real; histórico da origem preservado.", new_uuid[:8])

        last_capture_pct = -1
        deadline = time.monotonic() + DEADLINE_SECONDS
        last_status = None
        while time.monotonic() < deadline:
            response = requests.get(f"{NODE}/task/{new_uuid}/info", timeout=30)
            response.raise_for_status()
            info = response.json()
            code = (info.get("status") or {}).get("code")
            pct = float(info.get("progress") or 0)
            entry = {"observed_at": datetime.now().astimezone().isoformat(), "status_code": code, "progress_percent": pct,
                     "stage": (info.get("status") or {}).get("name")}
            if not manifest["progress_observations"] or code != last_status or pct >= (last_capture_pct + 10):
                manifest["progress_observations"].append(entry)
                print(json.dumps({"processing_id": new_id, **entry}, ensure_ascii=False), flush=True)
                if code != last_status or pct >= (last_capture_pct + 10) or code in {30, 40, 50}:
                    capture(page, manifest, f"progresso_{int(pct):03d}.png",
                            f"Recuperação real #'{new_id}' em {pct:.1f}% (estado NodeODM {code}); tarefa original #21 e produtos preservados.", new_uuid[:8])
                    last_capture_pct = pct
                last_status = code
            if code in {30, 40, 50}:
                break
            page.wait_for_timeout(POLL_SECONDS * 1000)
        else:
            raise TimeoutError(f"Recuperação excedeu {DEADLINE_SECONDS}s; a tarefa permanece {last_status}")

        manifest["recovery"]["nodeodm_terminal"] = info.get("status")
        manifest["recovery"]["progress"] = info.get("progress")
        manifest["recovery"]["processing_time_ms"] = info.get("processingTime")
        if code != 40:
            manifest["result"] = "FAIL_NODEODM_TERMINAL"
            save(manifest)
            raise RuntimeError(f"NodeODM terminou recuperação com status {info.get('status')}")

        task_row = page.locator(".task-row").filter(has_text=new_uuid[:8])
        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith(f"/api/odm/processamentos/{new_id}/importar"), timeout=60 * 60 * 1000) as import_event:
            task_row.get_by_role("button", name="Importar produtos", exact=True).click(timeout=60_000)
        imported_response = import_event.value
        if imported_response.status != 200:
            raise RuntimeError(f"Importação dos produtos recuperados falhou: HTTP {imported_response.status} {imported_response.text()[:700]}")
        imported_body = imported_response.json()
        imported_types = sorted({p["tipo"] for p in imported_body.get("produtos", [])})
        if not REQUIRED_PRODUCTS.issubset(imported_types):
            raise AssertionError(f"Produtos esperados não foram importados: {imported_types}")
        task_row = page.locator(".task-row").filter(has_text=new_uuid[:8])
        page.wait_for_timeout(1500)
        capture(page, manifest, "recuperacao_concluida_produtos_importados.png",
                "Recuperação concluída e seis produtos catalogados na nova tarefa.", new_uuid[:8])
        manifest["recovery"]["import_http"] = imported_response.status
        manifest["recovery"]["imported_product_types"] = imported_types
        manifest["recovery"]["page_errors"] = page_errors
        manifest["recovery"]["console_errors"] = console_errors
        if page_errors or console_errors:
            raise AssertionError(f"Erros do browser: page={page_errors}, console={console_errors}")
        browser.close()

    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id,status,parametros,odm_task_id FROM processamentos_odm WHERE id IN (%s,%s) ORDER BY id", (PARENT_ID, new_id))
        jobs = [dict(r) for r in cur.fetchall()]
        cur.execute("SELECT count(*) AS n FROM produtos_processamento WHERE processamento_id=%s", (PARENT_ID,))
        parent_count_after = int(cur.fetchone()["n"])
        cur.execute("SELECT count(*) AS n,coalesce(sum(tamanho_bytes),0) AS bytes FROM voo_fotos WHERE voo_id=%s", (parent["voo_id"],))
        photos_after = cur.fetchone()
        cur.execute("SELECT tipo,caminho FROM produtos_processamento WHERE processamento_id=%s", (new_id,))
        new_products = [dict(r) for r in cur.fetchall()]
    recovery_meta = jobs[1]["parametros"].get("recovery", {}) if isinstance(jobs[1]["parametros"], dict) else {}
    checks = {
        "source_stays_completed": jobs[0]["status"] == "concluido",
        "source_products_preserved": parent_count_after == len(parent_products) == 6,
        "source_photos_preserved": int(photos_after["n"]) == int(photos["n"]) == 77 and int(photos_after["bytes"]) == int(photos["bytes"]),
        "recovery_linked_to_source": recovery_meta.get("reprocessed_from_id") == PARENT_ID and recovery_meta.get("missing_task_id") == old_uuid,
        "recovery_task_completed": jobs[1]["status"] == "concluido" and (info.get("status") or {}).get("code") == 40,
        "all_six_product_types_imported": REQUIRED_PRODUCTS.issubset({p["tipo"] for p in new_products}),
        "browser_clean": not page_errors and not console_errors,
    }
    if not all(checks.values()):
        raise AssertionError(f"Checks UC-024 falharam: {checks}")
    manifest.update({
        "finished_at": datetime.now().astimezone().isoformat(),
        "recovery": {**manifest["recovery"], "recovery_metadata": recovery_meta,
                     "source_status_after": jobs[0]["status"], "new_status_after": jobs[1]["status"],
                     "source_product_count_after": parent_count_after,
                     "source_photo_count_after": int(photos_after["n"]), "source_photo_bytes_after": int(photos_after["bytes"]),
                     "new_catalog_product_count": len(new_products)},
        "acceptance_checks": checks,
        "page_errors": page_errors,
        "console_errors": console_errors,
        "result": "PASS_REAL_UC024_RECOVERY",
    })
    save(manifest)
    print(json.dumps({"result": manifest["result"], "source_processing_id": PARENT_ID,
                      "recovery_processing_id": new_id, "nodeodm_code": code,
                      "processing_time_ms": info.get("processingTime"), "products": imported_types,
                      "checks": checks, "manifest": str(OUT / "manifest.json")}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
