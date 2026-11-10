"""Validate ODM retry, conflict, cancel and recovery against a contract double.

The uploaded JPEGs are genuine GPS-tagged sample images, but this test does not
run photogrammetry. It exercises the app/API behavior with a local NodeODM API
contract fixture, after the real NodeODM processing was validated separately.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from urllib.error import HTTPError
from urllib.request import Request, urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
IMAGE_DIR = Path(os.getenv("ODM_ACCEPTANCE_IMAGES", ROOT / "data/odm_test/odm_data_aukerman-master/images"))
OUT = Path(os.getenv("ODM_ROBUSTNESS_OUT", ROOT / "docs/validacao/ortomapas_conclusao/etapa-03/robustez"))
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5179")
API = os.getenv("API_URL", "http://127.0.0.1:8889")
FIXTURE = "http://127.0.0.1:18022"


def multipart_post(url, fields, files, token, key):
    boundary = "----OrtomapasRobustez" + os.urandom(10).hex()
    body = []
    for name, value in fields.items():
        body.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(), str(value).encode(), b"\r\n"])
    for name, (filename, content, content_type) in files:
        body.extend([f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode(), f"Content-Type: {content_type}\r\n\r\n".encode(), content, b"\r\n"])
    body.append(f"--{boundary}--\r\n".encode())
    request = Request(url, data=b"".join(body), headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key, "Content-Type": f"multipart/form-data; boundary={boundary}"}, method="POST")
    try:
        with urlopen(request, timeout=240) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


def snap(page, manifest, name, note):
    OUT.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=True, animations="disabled")
    manifest["screenshots"].append({"file": f"{name}.png", "description": note})
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    photos = sorted(p for p in IMAGE_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg"})[:4]
    if len(photos) < 4:
        raise RuntimeError(f"Esperadas 4 fotos JPEG no conjunto de teste; encontradas {len(photos)}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    project_name = f"Aceite NodeODM Aukerman Fase3-Robustez-{stamp}"
    email = f"aceite-odm-Fase3-Robustez-{stamp}@example.test"
    password = f"Robustez-{stamp}-Teste!"
    manifest = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "project_name": project_name,
        "test_user_email": email,
        "dataset": str(IMAGE_DIR),
        "dataset_note": "Quatro JPEGs reais com metadados do conjunto público Aukerman; enviados ao double de contrato, sem processamento fotogramétrico.",
        "nodeodm_contract_fixture": FIXTURE,
        "screenshots": [],
        "assertions": [],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=os.getenv("CHROME_PATH", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        context = browser.new_context(viewport={"width": 1680, "height": 1050}, accept_downloads=True)
        page = context.new_page()
        page.set_default_timeout(45_000)
        page.goto(UI, wait_until="domcontentloaded")
        register = page.request.post(f"{API}/api/auth/register", data={"email": email, "nome": "Validação robustez ODM", "senha": password, "perfil": "pesquisador"})
        if register.status not in {201, 409}:
            raise RuntimeError(f"Cadastro temporário falhou: HTTP {register.status}")
        page.locator("input[type=email]").fill(email)
        page.locator("input[type=password]").fill(password)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.locator(".workspace-sidebar-nav").wait_for()
        page.get_by_role("button", name="Novo", exact=True).click()
        dialog = page.get_by_role("dialog", name="Novo Projeto")
        dialog.locator("input").nth(0).fill(project_name)
        dialog.locator("textarea").fill("Projeto isolado para validação de idempotência e recuperação ODM.")
        dialog.locator("input").nth(1).fill("Dataset público Aukerman (amostra de contrato)")
        dialog.get_by_role("button", name="Criar", exact=True).click()
        page.get_by_text(project_name, exact=True).wait_for()
        page.locator(".project-item").filter(has_text=project_name).click()
        token = page.evaluate("localStorage.getItem('ortomapas_token')")
        auth = {"Authorization": f"Bearer {token}"}
        project = next(x for x in page.request.get(f"{API}/api/projetos", headers=auth).json()["projetos"] if x["nome"] == project_name)
        project_id = project["id"]
        manifest.update(project_id=project_id, project_created=True)
        snap(page, manifest, "01_projeto_de_validacao", "Projeto descartável criado no app e selecionado; dataset descrito como amostra, sem confundir com voo real.")

        page.locator(".workspace-sidebar-nav").get_by_text("Voos e ODM", exact=True).click()
        page.get_by_role("button", name="Novo", exact=True).click()
        flight = page.get_by_role("dialog", name="Novo Voo")
        fields = flight.locator("input")
        fields.nth(0).fill(datetime.now().strftime("%Y-%m-%d"))
        fields.nth(1).fill("Aukerman contract fixture")
        fields.nth(2).fill("120")
        fields.nth(3).fill("4")
        flight.locator("textarea").fill("Fotos reais de amostra; API NodeODM substituída por fixture controlada; sem geração de ortomosaico.")
        flight.get_by_role("button", name="Criar", exact=True).click()
        page.get_by_text("Voo cadastrado no projeto.", exact=False).wait_for()
        row = page.locator(".voo-item").filter(has_text="Aukerman contract fixture")
        row.wait_for()
        voo = page.request.get(f"{API}/api/voos?projeto_id={project_id}", headers=auth).json()["voos"][0]
        manifest["voo_id"] = voo["id"]

        with page.expect_file_chooser() as chooser:
            row.get_by_role("button", name="Fotos", exact=True).click()
        chooser.value.set_files([str(p) for p in photos])
        upload = page.get_by_role("dialog", name="Processar fotos no ODM")
        snap(page, manifest, "02_fotos_e_parametros", "Quatro JPEGs do conjunto de amostra selecionados; tela do app pronta para enviar ao endpoint de contrato.")

        # Exercise a controlled upstream 503 through the visible UI, then retry
        # the same request in the same dialog so the browser reuses its key.
        page.request.post(f"{FIXTURE}/_test/fail-next", data="")
        with page.expect_response(lambda res: res.request.method == "POST" and res.url.endswith("/api/odm/tasks"), timeout=120_000) as failed_event:
            upload.get_by_role("button", name="Iniciar processamento").click()
        failed_response = failed_event.value
        if failed_response.status != 502:
            raise AssertionError(f"Esperado 502 controlado, obtido {failed_response.status}: {failed_response.text()[:300]}")
        snap(page, manifest, "03_erro_controlado", "NodeODM de contrato respondeu 503; o app informou falha sem apresentar sucesso falso.")
        with page.expect_response(lambda res: res.request.method == "POST" and res.url.endswith("/api/odm/tasks"), timeout=120_000) as retry_event:
            upload.get_by_role("button", name="Iniciar processamento").click()
        retry_response = retry_event.value
        request_key = retry_response.request.headers.get("idempotency-key")
        if retry_response.status != 202 or not request_key:
            raise AssertionError(f"Retry deveria retornar 202 com Idempotency-Key; HTTP {retry_response.status}")
        created = retry_response.json()
        processing_id = created["processamento_id"]
        task_id = created["task"]["uuid"]
        stats = page.request.get(f"{FIXTURE}/_test/stats").json()
        if stats["create_calls"] != 1 or stats["task_count"] != 1:
            raise AssertionError(f"Retry após falha criou quantidade inesperada de tarefas: {stats}")
        manifest["controlled_failure_and_retry"] = {"first_http": failed_response.status, "retry_http": retry_response.status, "retry_key_present": True, "fixture_create_calls": stats["create_calls"], "processing_id": processing_id, "task_id": task_id}
        manifest["assertions"].append({"case": "falha 503 e retry com a mesma chave", "expected": "nenhuma tarefa no primeiro envio; exatamente uma no retry", "observed": stats, "result": "PASS"})
        page.get_by_text("Processamento iniciado no NodeODM", exact=False).wait_for()
        snap(page, manifest, "04_retry_criou_uma_tarefa", "Retry após falha usa a chave retida pela interface e cria uma única tarefa no serviço de contrato.")

        # Replaying the same payload/key must reuse the local processing. A
        # different valid image under that key must be rejected with 409.
        files = [("images", (p.name, p.read_bytes(), "image/jpeg")) for p in photos]
        form = {"projeto_id": str(project_id), "voo_id": str(voo["id"]), "name": f"{project_name} - Voo {voo['id']}", "options": json.dumps([{"name": "dsm", "value": True}, {"name": "dtm", "value": True}, {"name": "pc-las", "value": True}])}
        replay_status, replay_text = multipart_post(f"{API}/api/odm/tasks", form, files, token, request_key)
        replay_body = json.loads(replay_text)
        if replay_status != 200 or not replay_body.get("reused") or replay_body.get("processamento_id") != processing_id:
            raise AssertionError(f"Replay idempotente falhou: HTTP {replay_status} {replay_text[:400]}")
        conflict_files = [("images", (p.name, p.read_bytes(), "image/jpeg")) for p in [*photos[:3], photos[4] if len(photos) > 4 else next(x for x in sorted(IMAGE_DIR.glob("*.JPG")) if x.name not in {q.name for q in photos})]]
        conflict_status, conflict_text = multipart_post(f"{API}/api/odm/tasks", form, conflict_files, token, request_key)
        if conflict_status != 409:
            raise AssertionError(f"Payload diferente deveria gerar 409; obtido HTTP {conflict_status}: {conflict_text[:300]}")
        stats = page.request.get(f"{FIXTURE}/_test/stats").json()
        if stats["create_calls"] != 1:
            raise AssertionError(f"Replay/conflito disparou tarefa duplicada: {stats}")
        manifest["idempotency"] = {"same_payload_http": replay_status, "same_payload_reused": replay_body.get("reused"), "reused_processing_id": replay_body.get("processamento_id"), "different_payload_http": conflict_status, "fixture_create_calls_after_both": stats["create_calls"]}
        manifest["assertions"].append({"case": "replay idempotente e chave conflitante", "expected": "200 reaproveitado para payload igual; 409 para payload diferente; 1 tarefa", "observed": manifest["idempotency"], "result": "PASS"})
        snap(page, manifest, "05_retry_idempotente_sem_duplicidade", "Replay do mesmo payload reaproveita o processo; alteração de fotos com a mesma chave é recusada.")

        page.get_by_role("button", name="Cancelar processamento", exact=True).click()
        dialog = page.get_by_role("dialog", name="Cancelar processamento ODM")
        snap(page, manifest, "06_confirmacao_cancelamento", "Confirmação mostra qual tarefa será cancelada e explica que produtos prévios serão preservados.")
        dialog.get_by_role("button", name="Confirmar cancelamento").click()
        page.get_by_text("Processamento cancelado no NodeODM.", exact=False).wait_for()
        canceled_info = page.request.get(f"{FIXTURE}/task/{task_id}/info").json()
        if canceled_info["status"]["code"] != 50:
            raise AssertionError(f"Fixture não confirmou cancelamento: {canceled_info}")
        manifest["cancel"] = {"fixture_status_code": canceled_info["status"]["code"], "processing_id": processing_id}
        manifest["assertions"].append({"case": "cancelamento", "expected": "POST cancel confirmado e estado terminal 50", "observed": manifest["cancel"], "result": "PASS"})
        snap(page, manifest, "07_cancelamento_confirmado", "Aplicação confirma o cancelamento e o contrato do NodeODM devolve estado terminal cancelado (50).")

        page.request.post(f"{FIXTURE}/task/remove", data={"uuid": task_id})
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline and not page.get_by_role("button", name="Reenviar fotos preservadas").count():
            page.wait_for_timeout(1500)
        recovery_button = page.get_by_role("button", name="Reenviar fotos preservadas")
        recovery_button.wait_for(timeout=5000)
        snap(page, manifest, "08_tarefa_ausente_com_recuperacao", "Histórico da tarefa foi removido do serviço de contrato; a interface identificou ausência e ofereceu recuperar as fotos preservadas.")
        recovery_button.click()
        recovery_dialog = page.get_by_role("dialog", name="Reenviar fotos ao NodeODM")
        snap(page, manifest, "09_confirmacao_recuperacao", "Diálogo informa que será criado novo processamento e que histórico/produtos anteriores permanecem preservados.")
        with page.expect_response(lambda res: res.request.method == "POST" and res.url.endswith(f"/api/odm/processamentos/{processing_id}/recuperar"), timeout=120_000) as recovered_event:
            recovery_dialog.get_by_role("button", name="Reenviar fotos").click()
        recovered = recovered_event.value
        if recovered.status != 202:
            raise AssertionError(f"Recuperação falhou: HTTP {recovered.status} {recovered.text()[:400]}")
        recovered_body = recovered.json()
        if recovered_body.get("images_count") != len(photos) or recovered_body.get("reprocessed_from_id") != processing_id:
            raise AssertionError(f"Recuperação não vinculou as fotos/origem esperadas: {recovered_body}")
        recovery_id, recovery_task_id = recovered_body["processing_id"], recovered_body["task"]["uuid"]
        stats = page.request.get(f"{FIXTURE}/_test/stats").json()
        if stats["create_calls"] != 2 or stats["task_count"] != 1:
            raise AssertionError(f"Recuperação não criou exatamente uma tarefa substituta: {stats}")
        manifest["recovery"] = {"http": recovered.status, "processing_id": recovery_id, "reprocessed_from_id": processing_id, "images_count": recovered_body["images_count"], "fixture_create_calls": stats["create_calls"]}
        manifest["assertions"].append({"case": "recuperação de tarefa ausente", "expected": "reenvia 4 fotos preservadas, cria novo processo e mantém registro antigo", "observed": manifest["recovery"], "result": "PASS"})
        page.get_by_text(f"Novo processamento {recovery_id} iniciado", exact=False).wait_for()
        snap(page, manifest, "10_recuperacao_concluida", "Novo processamento aparece após reenviar as quatro fotos locais preservadas; o vínculo aponta para a tarefa ausente.")

        # Cancel the replacement so no simulated work remains active.
        replacement = page.locator(".task-row").filter(has_text=recovery_task_id[:8])
        replacement.get_by_role("button", name="Cancelar processamento").click()
        replacement_dialog = page.get_by_role("dialog", name="Cancelar processamento ODM")
        replacement_dialog.get_by_role("button", name="Confirmar cancelamento").click()
        page.get_by_text("Processamento cancelado no NodeODM.", exact=False).wait_for()
        manifest.update(
            completed_at=datetime.now(timezone.utc).isoformat(),
            status="passed",
            processing_kind="NodeODM API contract fixture; no photogrammetry",
            task_ids=[task_id, recovery_task_id],
            processing_ids=[processing_id, recovery_id],
        )
        (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        browser.close()


if __name__ == "__main__":
    main()
