"""Resume monitoring/import of the already submitted real UC-024 recovery.

This script never submits a new task. It reads the UUID and processing ID from
the stage-10 manifest, follows the existing NodeODM task to code 40, imports
its six products in the UI, and checks the source processing/photos remain.
"""
from __future__ import annotations
import json, sys, time
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
from validate_uc024_real_recovery_phase10 import API, UI, NODE, PROJECT_ID, PARENT_ID, USER_ID, OUT, REQUIRED_PRODUCTS, save, capture, db_snapshot
POLL_SECONDS = 10
DEADLINE_SECONDS = 60 * 60

def main():
    manifest_path = OUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    recovery = manifest.get("recovery") or {}
    child_id, task_uuid = int(recovery["new_processing_id"]), recovery["new_task_uuid"]
    user, project, parent, photos, parent_products = db_snapshot()
    token = _token(user)
    headers = {"Authorization": f"Bearer {token}"}
    page_errors, console_errors = [], []
    listing = requests.get(f"{API}/api/odm/processamentos", params={"projeto_id": PROJECT_ID}, headers=headers, timeout=180)
    if listing.status_code != 200:
        raise RuntimeError(f"API não sincronizou a tarefa existente: HTTP {listing.status_code}")
    child_state = next((x for x in listing.json().get("processamentos", []) if int(x["id"]) == child_id), None)
    if not child_state or child_state.get("odm_task_id") != task_uuid:
        raise AssertionError(f"Não achei a tarefa #{child_id} no projeto: {child_state}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=which("google-chrome"), args=["--no-sandbox"])
        context = browser.new_context(viewport={"width":1680,"height":1100})
        context.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
        page = context.new_page(); page.set_default_timeout(60_000)
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.goto(UI, wait_until="domcontentloaded"); page.locator(".app-layout").wait_for(timeout=60_000)
        page.locator(".project-selector").click(); page.get_by_role("option", name=project["nome"], exact=True).click()
        page.get_by_role("button", name="Voos e ODM").click()
        row=page.locator(".task-row").filter(has_text=task_uuid[:8]); row.wait_for(timeout=60_000)
        last_pct = -1; last_code = None; deadline=time.monotonic()+DEADLINE_SECONDS
        while time.monotonic() < deadline:
            r=requests.get(f"{NODE}/task/{task_uuid}/info",timeout=30); r.raise_for_status(); info=r.json()
            code=(info.get("status") or {}).get("code"); pct=float(info.get("progress") or 0)
            if code not in {10,20,30,40,50}:
                raise RuntimeError(f"Estado NodeODM inesperado: {info}")
            if code != last_code or pct >= last_pct+10 or code in {30,40,50}:
                observation={"observed_at":datetime.now().astimezone().isoformat(),"status_code":code,"progress_percent":pct,"stage":(info.get("status") or {}).get("name"),"resumed_monitor":True}
                manifest.setdefault("progress_observations",[]).append(observation); print(json.dumps(observation,ensure_ascii=False),flush=True)
                capture(page,manifest,f"retomada_{int(pct):03d}.png",f"Continuação da recuperação real #{child_id}: {pct:.1f}% (status {code}).",task_uuid[:8])
                last_pct=pct; last_code=code
            if code in {30,40,50}: break
            page.wait_for_timeout(POLL_SECONDS*1000)
        else: raise TimeoutError("A tarefa recuperada ainda não atingiu estado terminal dentro de uma hora")
        manifest.setdefault("recovery",{}).update(nodeodm_terminal=info.get("status"),progress=info.get("progress"),processing_time_ms=info.get("processingTime"))
        save(manifest)
        if code != 40:
            manifest["result"]="FAIL_NODEODM_TERMINAL"; save(manifest)
            raise RuntimeError(f"Recuperação terminou sem sucesso: {info.get('status')}")
        row=page.locator(".task-row").filter(has_text=task_uuid[:8])
        with page.expect_response(lambda x:x.request.method=="POST" and x.url.endswith(f"/api/odm/processamentos/{child_id}/importar"),timeout=60*60*1000) as ev:
            row.get_by_role("button",name="Importar produtos",exact=True).click(timeout=60_000)
        imported_response=ev.value
        if imported_response.status!=200: raise RuntimeError(f"Importação HTTP {imported_response.status}: {imported_response.text()[:500]}")
        types=sorted({x["tipo"] for x in imported_response.json().get("produtos",[])})
        if not REQUIRED_PRODUCTS.issubset(types): raise AssertionError(f"Produtos incompletos: {types}")
        row=page.locator(".task-row").filter(has_text=task_uuid[:8]); page.wait_for_timeout(1500)
        capture(page,manifest,"recuperacao_concluida_produtos_importados.png","A tarefa recuperada concluiu e seus seis produtos estão catalogados.",task_uuid[:8])
        if page_errors or console_errors: raise AssertionError(f"Erros browser: {page_errors} {console_errors}")
        browser.close()
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute("SELECT id,status,parametros,odm_task_id FROM processamentos_odm WHERE id IN (%s,%s) ORDER BY id",(PARENT_ID,child_id)); jobs=[dict(x) for x in cur.fetchall()]
        cur.execute("SELECT count(*) AS n FROM produtos_processamento WHERE processamento_id=%s",(PARENT_ID,)); source_products=int(cur.fetchone()["n"])
        cur.execute("SELECT count(*) AS n,coalesce(sum(tamanho_bytes),0) AS bytes FROM voo_fotos WHERE voo_id=%s",(parent["voo_id"],)); photo_after=cur.fetchone()
        cur.execute("SELECT tipo FROM produtos_processamento WHERE processamento_id=%s",(child_id,)); product_types={x["tipo"] for x in cur.fetchall()}
    meta=jobs[1]["parametros"].get("recovery",{})
    checks={"source_completed":jobs[0]["status"]=="concluido","six_source_products_preserved":source_products==len(parent_products)==6,
      "77_source_photos_unchanged":int(photo_after["n"])==77==int(photos["n"]) and int(photo_after["bytes"])==int(photos["bytes"]),
      "lineage_preserved":meta.get("reprocessed_from_id")==PARENT_ID and meta.get("missing_task_id")==parent["odm_task_id"],
      "replacement_completed":jobs[1]["status"]=="concluido" and code==40,
      "six_recovered_product_types":REQUIRED_PRODUCTS.issubset(product_types),"browser_clean":not page_errors and not console_errors}
    if not all(checks.values()): raise AssertionError(f"UC-024 checks falharam: {checks}")
    manifest.update(finished_at=datetime.now().astimezone().isoformat(),recovery={**manifest["recovery"],"recovery_metadata":meta,
      "source_status_after":jobs[0]["status"],"new_status_after":jobs[1]["status"],"source_product_count_after":source_products,
      "source_photo_count_after":int(photo_after["n"]),"source_photo_bytes_after":int(photo_after["bytes"]),
      "import_http":imported_response.status,"imported_product_types":types,"new_catalog_product_count":len(product_types)},
      acceptance_checks=checks,page_errors=page_errors,console_errors=console_errors,result="PASS_REAL_UC024_RECOVERY")
    save(manifest)
    print(json.dumps({"result":manifest["result"],"source_processing_id":PARENT_ID,"recovery_processing_id":child_id,
      "nodeodm_code":code,"processing_time_ms":info.get("processingTime"),"products":types,"checks":checks,"manifest":str(manifest_path)},ensure_ascii=False,indent=2),flush=True)
if __name__=="__main__": main()
