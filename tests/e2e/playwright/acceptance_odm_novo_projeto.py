"""Long-running acceptance run: new project -> real photos -> NodeODM -> viewers.

Run with the repo's Playwright Python environment. The dedicated test account is
registered through the app's public registration endpoint and credentials are
kept only in memory. Screenshots and a JSON manifest are written under docs.
"""
from __future__ import annotations

import json
import os
import sys
import time
from shutil import which
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
IMAGE_DIR = Path(os.getenv("ODM_ACCEPTANCE_IMAGES", ROOT / "data/odm_test/odm_data_aukerman-master/images"))
OUT = Path(os.getenv("ODM_ACCEPTANCE_OUT", ROOT / "docs/validacao/odm_operacao_2026-11-05/aceite_projeto_novo"))
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176")
API = os.getenv("API_URL", "http://127.0.0.1:8888")
MAX_WAIT_S = int(os.getenv("ODM_ACCEPTANCE_MAX_WAIT_S", "10800"))


def log(message: str):
    print(f"[{datetime.now().astimezone().isoformat(timespec='seconds')}] {message}", flush=True)


def save_manifest(manifest):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def screenshot(page, name, manifest, description):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=True, animations="disabled")
    manifest.setdefault("screenshots", []).append({"file": path.name, "description": description})
    save_manifest(manifest)
    log(f"Captura: {path.name} — {description}")


def api_json(page, method, url, data=None, timeout=120_000):
    token = page.evaluate("localStorage.getItem('ortomapas_token')")
    response = getattr(page.request, method.lower())(url, data=data, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=timeout)
    body = response.json() if response.ok else response.text()
    if not response.ok:
        raise RuntimeError(f"{method} {url}: HTTP {response.status} {body}")
    return body


def multipart_post(url, fields, files, token, timeout=60):
    """Small stdlib multipart helper for a rejected upload negative case."""
    boundary = "----OrtomapasPhase3" + os.urandom(12).hex()
    chunks = []
    for name, value in fields.items():
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode(),
            str(value).encode(), b"\r\n",
        ])
    for field_name, filename, content_type, content in files:
        chunks.extend([
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'.encode(),
            f"Content-Type: {content_type}\r\n\r\n".encode(),
            content, b"\r\n",
        ])
    chunks.append(f"--{boundary}--\r\n".encode())
    request = Request(
        url,
        data=b"".join(chunks),
        headers={"Authorization": f"Bearer {token}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8", "replace")


def main():
    images = sorted(p for p in IMAGE_DIR.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".tif", ".tiff"})
    if len(images) < 3:
        raise RuntimeError(f"Dataset insuficiente em {IMAGE_DIR}: {len(images)} fotos")

    now = datetime.now(timezone.utc)
    prior_path = OUT / "manifest.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8")) if prior_path.exists() else {}
    stamp = now.strftime("%Y%m%d-%H%M%S")
    project_name = os.getenv("ODM_ACCEPTANCE_PROJECT_NAME") or prior.get("project_name") or f"Aceite NodeODM Aukerman {stamp}"
    prior_stamp = project_name.removeprefix("Aceite NodeODM Aukerman ")
    email = os.getenv("ODM_ACCEPTANCE_EMAIL") or prior.get("test_user_email") or f"aceite-odm-{prior_stamp}@example.test"
    password = os.getenv("ODM_ACCEPTANCE_PASSWORD") or f"Orto-{prior_stamp}-Aceite!"
    flight_name = f"Dataset público Aukerman — validação fotogramétrica"
    manifest = {
        **prior,
        "started_at": now.isoformat(),
        "ui": UI,
        "api": API,
        "dataset": str(IMAGE_DIR),
        "image_count": len(images),
        "dataset_note": "Imagens públicas Aukerman do ODM; não representam Guarajuba nem voo executado nesta validação.",
        "project_name": project_name,
        "test_user_email": email,
        "flight_name": flight_name,
        "screenshots": [],
        "events": [],
    }
    save_manifest(manifest)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=os.getenv("CHROME_PATH") or which("google-chrome") or which("chromium"),
            args=["--no-sandbox"],
        )
        context = browser.new_context(viewport={"width": 1680, "height": 1050}, accept_downloads=True)
        page = context.new_page()
        browser_page_errors = []
        page.on("pageerror", lambda error: browser_page_errors.append(str(error)))
        page.set_default_timeout(45_000)
        page.goto(UI, wait_until="domcontentloaded")

        # Create an isolated user via the app itself, then log in through its UI.
        reg = page.request.post(f"{API}/api/auth/register", data={"email": email, "nome": "Validação automatizada ODM", "senha": password, "perfil": "pesquisador"}, timeout=30_000)
        if reg.status not in {201, 409}:
            raise RuntimeError(f"Cadastro da conta isolada falhou: HTTP {reg.status} {reg.text()}")
        page.locator("input[type=email]").fill(email)
        page.locator("input[type=password]").fill(password)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.locator(".workspace-sidebar-nav").wait_for()
        screenshot(page, "01_aplicativo_logado", manifest, "Login realizado na interface com uma conta de validação recém-criada.")

        # Create the project using the visible project form, or resume the one
        # saved in the manifest if a prior browser step was interrupted.
        project = api_json(page, "GET", f"{API}/api/projetos")
        projects = project.get("projetos", project if isinstance(project, list) else [])
        project_record = next((item for item in projects if item.get("nome") == project_name), None)
        if not project_record:
            page.get_by_role("button", name="Novo", exact=True).click()
            dialog = page.get_by_role("dialog", name="Novo Projeto")
            dialog.locator("input").nth(0).fill(project_name)
            dialog.locator("textarea").fill("Projeto novo para validar o ciclo completo com imagens públicas Aukerman; não é captura de Guarajuba.")
            dialog.locator("input").nth(1).fill("Dataset público Aukerman (área de teste)")
            screenshot(page, "02_novo_projeto_preenchido", manifest, "Formulário de projeto preenchido antes de salvar; a área está identificada como dataset de teste.")
            dialog.get_by_role("button", name="Criar", exact=True).click()
            page.get_by_text(project_name, exact=True).wait_for()
            dialog.wait_for(state="hidden", timeout=20_000)
            project_item = page.locator(".project-item").filter(has_text=project_name)
            project_item.click()
            page.wait_for_function("""name => document.body.innerText.includes(name) && document.body.innerText.includes('Nenhum ortomapa carregado')""", arg=project_name)
            project = api_json(page, "GET", f"{API}/api/projetos")
            projects = project.get("projetos", project if isinstance(project, list) else [])
            project_record = next((item for item in projects if item.get("nome") == project_name), None)
        else:
            page.get_by_text(project_name, exact=True).first.click()
            page.wait_for_timeout(1500)
        if not project_record:
            raise RuntimeError("Projeto recém-criado não apareceu na consulta autenticada")
        project_id = project_record["id"]
        manifest.update(project_id=project_id, project_created=True)
        screenshot(page, "03_projeto_novo_vazio", manifest, f"Projeto #{project_id} selecionado, ainda sem voos ou ortomapas.")

        # Create a flight and attach the real sample photos via the file input.
        page.locator(".workspace-sidebar-nav").get_by_text("Voos e ODM", exact=True).click()
        page.get_by_role("button", name="Novo", exact=True).click()
        flight_dialog = page.get_by_role("dialog", name="Novo Voo")
        inputs = flight_dialog.locator("input")
        inputs.nth(0).fill(datetime.now().strftime("%Y-%m-%d"))
        inputs.nth(1).fill("Aukerman ODM public sample (not a drone flight)")
        inputs.nth(2).fill("120")
        inputs.nth(3).fill(str(len(images)))
        flight_dialog.locator("textarea").fill("Dataset público ODM Aukerman para teste de processamento. Não corresponde a voo realizado nem à área de Guarajuba.")
        screenshot(page, "04_novo_voo_preenchido", manifest, "Cadastro do voo de teste com origem do dataset explicitada e 77 fotos esperadas.")
        flight_dialog.get_by_role("button", name="Criar", exact=True).click()
        page.get_by_text("Voo cadastrado no projeto.", exact=False).wait_for(timeout=45_000)
        flight_row = page.locator(".voo-item").filter(has_text="Aukerman ODM public sample")
        flight_row.wait_for()
        voo_id = api_json(page, "GET", f"{API}/api/voos?projeto_id={project_id}")["voos"][0]["id"]
        manifest.update(voo_id=voo_id, flight_created=True)
        screenshot(page, "05_voo_cadastrado", manifest, f"Voo de teste #{voo_id} registrado no projeto.")

        # Negative upload must stop before creating a NodeODM task or
        # persisting flight photos. Three parts pass the count guard; the first
        # unsupported extension should be rejected by the API.
        token = page.evaluate("localStorage.getItem('ortomapas_token')")
        before_invalid = api_json(page, "GET", f"{API}/api/odm/processamentos?projeto_id={project_id}")
        invalid_status, invalid_body = multipart_post(
            f"{API}/api/odm/tasks",
            {"projeto_id": project_id, "voo_id": voo_id, "name": "invalid-upload-negative-test"},
            [
                ("images", "bad.txt", "text/plain", b"not an image"),
                ("images", "sample-1.jpg", "image/jpeg", b"not uploaded after first rejection"),
                ("images", "sample-2.jpg", "image/jpeg", b"not uploaded after first rejection"),
            ],
            token,
        )
        after_invalid = api_json(page, "GET", f"{API}/api/odm/processamentos?projeto_id={project_id}")
        if invalid_status != 400 or len(after_invalid["processamentos"]) != len(before_invalid["processamentos"]):
            raise RuntimeError(f"Upload inválido não foi rejeitado sem criar tarefa: HTTP {invalid_status} {invalid_body[:300]}")
        try:
            invalid_detail = json.loads(invalid_body).get("detail")
        except ValueError:
            invalid_detail = invalid_body[:300]
        manifest["invalid_upload_test"] = {
            "expected_http": 400,
            "observed_http": invalid_status,
            "message": invalid_detail,
            "processing_count_before": len(before_invalid["processamentos"]),
            "processing_count_after": len(after_invalid["processamentos"]),
        }
        log("Entrada .txt rejeitada antes de criar tarefa NodeODM ou associar fotos.")

        with page.expect_file_chooser() as chooser_info:
            flight_row.get_by_role("button", name="Fotos", exact=True).click()
        chooser_info.value.set_files([str(path) for path in images], timeout=120_000)
        upload_dialog = page.get_by_role("dialog", name="Processar fotos no ODM")
        upload_dialog.wait_for()
        screenshot(page, "06_fotos_selecionadas", manifest, "As 77 fotografias reais do dataset estão selecionadas; opções completas de reconstrução habilitadas.")

        started = time.monotonic()
        with page.expect_response(lambda response: response.request.method == "POST" and response.url.endswith("/api/odm/tasks"), timeout=900_000) as submit_info:
            upload_dialog.get_by_role("button", name="Iniciar processamento", exact=True).click(timeout=120_000)
        submit_response = submit_info.value
        submit_body = submit_response.json()
        if submit_response.status != 202:
            raise RuntimeError(f"NodeODM não aceitou o upload: HTTP {submit_response.status} {submit_body}")
        task_id = submit_body["task"]["uuid"]
        processing_id = submit_body["processamento_id"]
        manifest.update(task_id=task_id, processing_id=processing_id, accepted_images=submit_body.get("images_count"), geotagged_images=submit_body.get("geotagged_count"), upload_seconds=round(time.monotonic() - started, 2), processing_started_at=datetime.now(timezone.utc).isoformat())
        log(f"NodeODM aceitou {submit_body.get('images_count')} fotos; tarefa {task_id}, processamento local {processing_id}.")
        screenshot(page, "07_tarefa_nodeodm_enviada", manifest, f"Upload aceito pelo NodeODM; UUID {task_id}.")

        # Poll the local project-scoped task list. Persist heartbeats for recovery.
        deadline = time.monotonic() + MAX_WAIT_S
        last_heartbeat = 0.0
        captured = set()
        final_job = None
        while time.monotonic() < deadline:
            result = api_json(page, "GET", f"{API}/api/odm/processamentos?projeto_id={project_id}")
            final_job = next((job for job in result["processamentos"] if job["id"] == processing_id), None)
            if not final_job:
                raise RuntimeError("A tarefa aceita não aparece no histórico ODM do projeto")
            progress = float(final_job.get("progresso") or 0)
            state = final_job.get("status")
            manifest["processing_latest"] = {"status": state, "progress": progress, "stage": final_job.get("etapa"), "checked_at": datetime.now(timezone.utc).isoformat()}
            if state == "processando" and "processing" not in captured:
                page.locator(".task-row").wait_for()
                screenshot(page, "08_processamento_em_andamento", manifest, f"Tarefa real em processamento no NodeODM: etapa {final_job.get('etapa')}, progresso {progress:.0f}%.")
                captured.add("processing")
            for threshold, key, file in [(25, "p25", "09_progresso_25"), (75, "p75", "10_progresso_75")]:
                if progress >= threshold and key not in captured:
                    page.locator(".task-row").wait_for()
                    screenshot(page, file, manifest, f"NodeODM processando; progresso reportado pelo serviço {progress:.0f}%.")
                    captured.add(key)
            if state in {"concluido", "erro", "cancelado"}:
                break
            if time.monotonic() - last_heartbeat >= 30:
                save_manifest(manifest)
                log(f"NodeODM: {state}, {progress:.1f}%, etapa={final_job.get('etapa') or 'aguardando'}")
                last_heartbeat = time.monotonic()
            time.sleep(12)
        if not final_job or final_job.get("status") != "concluido":
            manifest["processing_terminal"] = final_job
            save_manifest(manifest)
            raise RuntimeError(f"NodeODM terminou sem sucesso ou excedeu o prazo: {final_job}")

        manifest["processing_terminal"] = {"status": final_job["status"], "progress": final_job.get("progresso"), "stage": final_job.get("etapa"), "duration_minutes": round((time.monotonic() - started) / 60, 2)}
        screenshot(page, "11_processamento_concluido", manifest, f"NodeODM marcou a tarefa como concluída; duração total desde o upload: {manifest['processing_terminal']['duration_minutes']} min.")

        task_row = page.locator(".task-row").filter(has_text=task_id[:8])
        task_row.wait_for()
        with page.expect_response(lambda response: response.request.method == "POST" and response.url.endswith(f"/api/odm/processamentos/{processing_id}/importar"), timeout=900_000) as import_info:
            task_row.get_by_role("button", name="Importar produtos", exact=True).click()
        import_response = import_info.value
        imported = import_response.json()
        if import_response.status != 200:
            raise RuntimeError(f"Falha ao importar produtos: HTTP {import_response.status} {imported}")
        manifest["imported_products"] = imported.get("produtos", [])
        products = imported.get("produtos", [])
        types = {product["tipo"] for product in products}
        manifest["product_types"] = sorted(types)
        expected = {"ortomosaico", "dsm", "dtm", "relatorio", "nuvem_pontos", "modelo_3d"}
        manifest["product_type_coverage"] = {key: key in types for key in sorted(expected)}
        if "ortomosaico" not in types or "dsm" not in types or "dtm" not in types:
            raise RuntimeError(f"Produtos essenciais ausentes: {types}")
        page.wait_for_timeout(2500)
        screenshot(page, "12_catalogo_produtos_importados", manifest, "Catálogo após importação de ortofoto, DSM, DTM, relatório, nuvem de pontos e modelo texturizado, conforme disponibilidade do processamento.")

        # Open the actual orthomosaic on the map and wait for server-produced tiles.
        task_row.get_by_role("button", name="Abrir ortofoto", exact=True).click()
        page.wait_for_timeout(8000)
        manifest["ortho_tiles_loaded"] = page.locator(".leaflet-tile-loaded").count()
        screenshot(page, "13_ortomosaico_no_mapa", manifest, f"Ortomosaico real adicionado ao mapa; tiles carregados: {manifest['ortho_tiles_loaded']}.")

        # Open/inspect actual textured mesh, DSM, DTM, cloud and DSM-DTM difference.
        if "modelo_3d" in types:
            task_row.get_by_role("button", name="Modelo texturizado 3D", exact=True).click()
            page.locator(".model-view .canvas-host").wait_for()
            page.wait_for_function("""() => { const s=document.querySelector('.model-view .canvas-host')?.dataset.modelState; return s && s !== 'loading' }""", timeout=180_000)
            mesh_state = page.locator(".model-view .canvas-host").get_attribute("data-model-state")
            manifest["textured_model_state"] = mesh_state
            if mesh_state != "loaded":
                raise RuntimeError("Modelo 3D texturizado não foi renderizado: " + (page.locator(".model-view [role=alert]").inner_text() if page.locator(".model-view [role=alert]").count() else mesh_state))
            manifest["textured_model_footer"] = page.locator(".model-view footer").inner_text()
            screenshot(page, "14_modelo_texturizado_3d", manifest, "Modelo GLB real renderizado em WebGL; rodapé informa métricas de geometria e materiais.")
            # This canvas modal does not implement Escape. Close it through its
            # explicit control and wait before clicking the next product row.
            page.locator('.model-view button[title="Fechar"]').click()
            page.locator(".model-view").wait_for(state="detached")

        if "dsm" in types:
            task_row.get_by_role("button", name="DSM 3D", exact=True).click()
            page.locator(".surface-view").wait_for(timeout=30_000)
            page.wait_for_timeout(3000)
            screenshot(page, "15_dsm_superficie_3d", manifest, "DSM gerado pelo NodeODM aberto no visualizador de superfície 3D.")
            page.locator('.surface-view button[title="Fechar"]').click()
            page.locator(".surface-view").wait_for(state="detached")
        if "dtm" in types:
            task_row.get_by_role("button", name="DTM 3D", exact=True).click()
            page.locator(".surface-view").wait_for(timeout=30_000)
            page.wait_for_timeout(3000)
            screenshot(page, "16_dtm_terreno_3d", manifest, "DTM gerado pelo NodeODM aberto no visualizador de terreno 3D.")
            page.locator('.surface-view button[title="Fechar"]').click()
            page.locator(".surface-view").wait_for(state="detached")
        if "nuvem_pontos" in types:
            task_row.get_by_role("button", name="Abrir 3D", exact=True).click()
            page.locator(".viewer-shell").wait_for(timeout=30_000)
            page.wait_for_timeout(5000)
            screenshot(page, "17_nuvem_pontos_3d", manifest, "Nuvem de pontos fotogramétrica aberta no visualizador 3D.")
            page.locator('.viewer-shell button[title="Fechar"]').click()
            page.locator(".viewer-shell").wait_for(state="detached")
        if {"dsm", "dtm"}.issubset(types):
            task_row.get_by_role("button", name="Diferença", exact=True).click()
            page.locator(".diff-view").wait_for(timeout=30_000)
            page.wait_for_timeout(3000)
            screenshot(page, "18_diferenca_dsm_dtm", manifest, "Diferença entre DSM e DTM aberta para comparar superfície e terreno.")
            page.locator('.diff-view button[title="Fechar diferenca"]').click()
            page.locator(".diff-view").wait_for(state="detached")
        task_row.locator('button[title="Avaliar qualidade"]').click()
        page.locator(".quality-row").wait_for(timeout=30_000)
        manifest["quality_text"] = task_row.locator(".quality-row").inner_text()
        screenshot(page, "19_qualidade_do_processamento", manifest, "Avaliação operacional de qualidade exibida para a tarefa concluída.")

        # Run and persist real slope raster via the spatial-analysis UI.
        page.locator(".workspace-sidebar-nav").get_by_text("Análises", exact=True).click()
        page.locator(".tools-panel").get_by_text("Ter", exact=True).click()
        page.get_by_role("button", name="Gerar Analise", exact=True).click(timeout=60_000)
        result_panel = page.locator(".terrain-result")
        result_panel.wait_for(timeout=900_000)
        manifest["slope_result_ui"] = result_panel.inner_text()
        manifest["slope_analysis_api"] = api_json(page, "GET", f"{API}/api/analises?projeto_id={project_id}&tipo_analise=terreno")
        manifest["browser_page_errors"] = browser_page_errors
        screenshot(page, "20_analise_declividade_resultado", manifest, "Declividade calculada sobre o DSM, publicada no mapa e salva no catálogo de análises do projeto.")
        if not manifest["slope_analysis_api"].get("analises"):
            raise RuntimeError("Declividade foi exibida mas não apareceu persistida no catálogo de análises")
        if browser_page_errors:
            raise RuntimeError(f"Erros JavaScript durante o aceite integrado: {browser_page_errors}")

        manifest.update(finished_at=datetime.now(timezone.utc).isoformat(), outcome="passed")
        save_manifest(manifest)
        log(f"Aceitação concluída: projeto={project_id}, voo={voo_id}, processamento={processing_id}, tarefa={task_id}; produtos={sorted(types)}")
        browser.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        failure = {"outcome": "failed", "failed_at": datetime.now(timezone.utc).isoformat(), "error": f"{type(exc).__name__}: {exc}"}
        existing = {}
        manifest_path = OUT / "manifest.json"
        if manifest_path.exists():
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        existing.update(failure)
        save_manifest(existing)
        log(f"FALHA: {failure['error']}")
        raise
