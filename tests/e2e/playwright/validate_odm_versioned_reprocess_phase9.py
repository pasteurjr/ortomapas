"""Exercise versioned reprocessing and cancellation against the real NodeODM.

Uses the already completed public Aukerman project #88 as the immutable parent,
retains the original 77-photo flight, changes orthophoto resolution, then
cancels the new live NodeODM task to avoid a second long photogrammetry run.
The short-lived signed token is held in memory only.
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
from backend.database.connection import get_connection
from backend.routers.auth import _token

UI = "http://127.0.0.1:5176"
API = "http://127.0.0.1:8888"
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-09/playwright/uc024_029"
PROJECT_ID = 88
PARENT_ID = 21
USER_ID = 60


def main():
    OUT.mkdir(parents=True, exist_ok=True)
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
        cur.execute("SELECT count(*) AS n FROM produtos_processamento WHERE processamento_id=%s", (PARENT_ID,))
        parent_products_before = cur.fetchone()["n"]
        cur.execute("""SELECT COALESCE(MAX(NULLIF(parametros->'reprocessamento'->>'version','')::INTEGER),1) AS latest
            FROM processamentos_odm WHERE id=%s OR parametros->'reprocessamento'->>'root_processing_id'=%s""",
                    (PARENT_ID, str(PARENT_ID)))
        expected_version = int(cur.fetchone()["latest"]) + 1
    if not user or not project or not parent or parent["status"] != "concluido":
        raise RuntimeError("Projeto/usuário ou processamento original concluído não está disponível")
    if photos["n"] < 3:
        raise RuntimeError("O voo original não possui fotos suficientes preservadas")

    token = _token(user)
    manifest = {
        "started_at": datetime.now().astimezone().isoformat(),
        "environment": {"ui": UI, "api": API, "nodeodm": "real NodeODM 2.2.4 / ODM 3.5.6"},
        "project_id": PROJECT_ID,
        "parent_processing_id": PARENT_ID,
        "parent_status_before": parent["status"],
        "preserved_photo_count": photos["n"],
        "preserved_photo_bytes": int(photos["bytes"]),
        "parent_product_count_before": parent_products_before,
        "expected_new_version": expected_version,
        "changed_parameter": {"name": "orthophoto-resolution", "old": "not set (ODM default)", "new": 10, "unit": "cm/pixel"},
        "screenshots": [],
        "assertions": [],
        "page_errors": [],
        "console_errors": [],
        "llm_calls": 0,
    }
    api_responses = []
    idem_headers = []

    def screenshot(page, name, description):
        page.screenshot(path=str(OUT / f"{name}.png"), full_page=True, animations="disabled")
        manifest["screenshots"].append({"file": f"{name}.png", "description": description})
        (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=which("google-chrome"), args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1660, "height": 1080}, accept_downloads=True)
        context.add_init_script("localStorage.setItem('ortomapas_token', " + json.dumps(token) + ");")
        page = context.new_page()
        page.set_default_timeout(40_000)
        page.on("pageerror", lambda exc: manifest["page_errors"].append(str(exc)))
        page.on("console", lambda msg: manifest["console_errors"].append(msg.text) if msg.type == "error" else None)
        page.on("request", lambda req: idem_headers.append(req.headers.get("idempotency-key"))
                if req.method == "POST" and req.url.endswith(f"/api/odm/processamentos/{PARENT_ID}/reprocessar") else None)
        page.on("response", lambda res: api_responses.append({"status": res.status, "url": res.url.split("?")[0]})
                if "/api/odm/" in res.url else None)

        page.goto(UI, wait_until="domcontentloaded")
        page.locator(".app-layout").wait_for(timeout=30_000)
        project_select = page.locator(".project-selector")
        project_select.click()
        page.get_by_role("option", name=project["nome"], exact=True).click()
        page.get_by_role("button", name="Voos e ODM").click()
        parent_row = page.locator(".task-row").filter(has_text=parent["odm_task_id"][:8])
        parent_row.wait_for()
        page.get_by_role("button", name="Criar nova versão").first.wait_for()
        screenshot(page, "01_processamento_original_concluido", "Processamento original #21 concluído e ação para abrir uma versão independente disponível.")

        parent_row.get_by_role("button", name="Criar nova versão").click()
        dialog = page.get_by_role("dialog", name="Reprocessar com novos parâmetros")
        dialog.wait_for()
        resolution = dialog.locator("#reprocess-ortho-resolution")
        resolution.fill("10")
        screenshot(page, "02_confirmacao_novos_parametros", "Confirmação mostra que o original e seus produtos serão preservados; resolução nova de 10 cm/pixel.")

        with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith(f"/api/odm/processamentos/{PARENT_ID}/reprocessar"), timeout=600_000) as event:
            dialog.get_by_role("button", name="Criar nova versão").click()
        created_response = event.value
        if created_response.status != 202:
            raise RuntimeError(f"Reprocessamento real falhou: HTTP {created_response.status}: {created_response.text()[:500]}")
        created = created_response.json()
        child_id = created["processing_id"]
        task_uuid = created["task"]["uuid"]
        if created["reprocessed_from_id"] != PARENT_ID or created["version"] != expected_version or created["images_count"] != photos["n"]:
            raise AssertionError(f"A nova versão não preservou origem/versão/fotos: {created}")
        manifest["reprocess"] = {key: created[key] for key in ("processing_id", "reprocessed_from_id", "root_processing_id", "version", "images_count", "total_bytes", "reused")}
        manifest["idempotency_key_captured"] = bool(idem_headers and idem_headers[-1])
        manifest["assertions"].append({"case": "nova versão ODM real", "expected": f"nova tarefa NodeODM 202 com pai #21, versão {expected_version}, novas opções e todas as fotos preservadas", "observed": manifest["reprocess"], "result": "PASS"})

        token_headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": idem_headers[-1]}
        duplicate = page.request.post(f"{API}/api/odm/processamentos/{PARENT_ID}/reprocessar", headers=token_headers,
                                      data={"options": [{"name": "orthophoto-resolution", "value": 10}]})
        if duplicate.status != 200 or duplicate.json().get("processing_id") != child_id or not duplicate.json().get("reused"):
            raise AssertionError(f"Retry com a mesma Idempotency-Key não foi idempotente: HTTP {duplicate.status} {duplicate.text()[:400]}")
        conflict = page.request.post(f"{API}/api/odm/processamentos/{PARENT_ID}/reprocessar", headers=token_headers,
                                     data={"options": [{"name": "orthophoto-resolution", "value": 12}]})
        if conflict.status != 409:
            raise AssertionError(f"Reuso de chave com parâmetros diferentes deveria retornar 409, veio {conflict.status}")
        manifest["idempotency"] = {"same_payload_status": duplicate.status, "same_processing_id": duplicate.json().get("processing_id"), "changed_payload_status": conflict.status}
        manifest["assertions"].append({"case": "idempotência de reprocessamento", "expected": "mesma chave e payload reutilizam a tarefa; payload diferente conflita", "observed": manifest["idempotency"], "result": "PASS"})
        page.get_by_text(f"Versão {expected_version} criada como processamento #{child_id}", exact=False).wait_for(timeout=30_000)
        child_row = page.locator(".task-row").filter(has_text=task_uuid[:8])
        child_row.wait_for(timeout=30_000)
        screenshot(page, "03_nova_versao_na_fila_nodeodm", "Nova tarefa real aparece no histórico com versão e origem; a antiga permanece concluída.")

        info = None
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            resp = requests.get(f"http://127.0.0.1:8021/task/{task_uuid}/info", timeout=8)
            if resp.ok:
                info = resp.json()
                if (info.get("status") or {}).get("code") in {10, 20}:
                    break
                if (info.get("status") or {}).get("code") in {30, 40, 50}:
                    raise RuntimeError(f"Tarefa terminou antes da ação de cancelamento: {info.get('status')}")
            time.sleep(1)
        if not info or (info.get("status") or {}).get("code") not in {10, 20}:
            raise RuntimeError("Nova tarefa não ficou em estado ativo a tempo de validar cancelamento")

        child_row.get_by_role("button", name="Cancelar processamento").click()
        cancel_dialog = page.get_by_role("dialog", name="Cancelar processamento ODM")
        screenshot(page, "04_confirmacao_cancelamento_nova_versao", "Confirmação identifica a tarefa nova que será cancelada.")
        cancel_dialog.get_by_role("button", name="Confirmar cancelamento").click()
        page.get_by_text("Processamento cancelado no NodeODM.", exact=False).wait_for(timeout=60_000)
        child_row.get_by_text("Cancelado", exact=False).wait_for(timeout=30_000)
        child_row.get_by_text("Interrompido", exact=False).wait_for()
        child_row.get_by_text("Execução interrompida; os produtos desta versão não foram gerados.", exact=True).wait_for()
        screenshot(page, "05_cancelamento_confirmado_historico_preservado", "A nova versão termina cancelada; a versão original permanece concluída e separada.")
        manifest["assertions"].append({"case": "representação visual do cancelamento", "expected": "sem barra de progresso 100%; indicar interrupção e ausência de produtos", "observed": "mensagem explícita visível na captura 05; sem erro JS", "result": "PASS"})

        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id,status,parametros,engine,engine_version FROM processamentos_odm WHERE id IN (%s,%s) ORDER BY id", (PARENT_ID, child_id))
            rows = [dict(row) for row in cur.fetchall()]
            cur.execute("SELECT count(*) AS n FROM produtos_processamento WHERE processamento_id=%s", (PARENT_ID,))
            products_after = cur.fetchone()["n"]
            cur.execute("SELECT count(*) AS n FROM produtos_processamento WHERE processamento_id=%s", (child_id,))
            child_products = cur.fetchone()["n"]
        remote_final = requests.get(f"http://127.0.0.1:8021/task/{task_uuid}/info", timeout=15).json()
        if rows[0]["status"] != "concluido" or rows[1]["status"] != "cancelado":
            raise AssertionError(f"Estados finais inesperados no banco: {[row['status'] for row in rows]}")
        if products_after != parent_products_before or child_products != 0 or (remote_final.get("status") or {}).get("code") != 50:
            raise AssertionError("Cancelamento alterou produtos originais ou NodeODM não confirmou código 50")
        child_parameters = rows[1]["parametros"]
        if child_parameters.get("reprocessamento", {}).get("parent_processing_id") != PARENT_ID or child_parameters.get("reprocessamento", {}).get("version") != expected_version:
            raise AssertionError(f"Metadados de linhagem da nova versão não persistidos: {child_parameters}")
        manifest["final"] = {
            "parent_status": rows[0]["status"], "child_status": rows[1]["status"],
            "nodeodm_status_code": remote_final["status"]["code"],
            "parent_product_count_before": parent_products_before, "parent_product_count_after": products_after,
            "child_product_count": child_products,
            "engine": rows[1]["engine"], "engine_version": rows[1]["engine_version"],
            "child_options": child_parameters["options"],
            "page_errors": manifest["page_errors"], "console_errors": manifest["console_errors"],
            "api_responses": api_responses,
        }
        manifest["assertions"].append({"case": "cancelamento sem perda de histórico/produtos", "expected": "NodeODM status 50, nova versão cancelada, pai concluído e produtos anteriores intactos", "observed": manifest["final"], "result": "PASS"})
        if manifest["page_errors"] or manifest["console_errors"]:
            raise AssertionError(f"Erros do navegador: {manifest['page_errors']} {manifest['console_errors']}")
        (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        browser.close()
    print(json.dumps({"manifest": str((OUT / "manifest.json").relative_to(ROOT)),
                      "screenshots": [item["file"] for item in manifest["screenshots"]],
                      "final": manifest["final"], "assertions": manifest["assertions"]}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
