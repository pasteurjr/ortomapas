"""Disposable two-account UI/API isolation check for Ortomapas Phase 2.

Run only against the configured local validation database and a local API/Vite.
The script creates uniquely named temporary users/project, records screenshots,
and removes the records/files in a finally block. It never invokes an LLM.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import subprocess
from shutil import which
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
API = os.getenv("API_URL", "http://127.0.0.1:8888/api").rstrip("/")
WEB = os.getenv("WEB_URL", "http://127.0.0.1:5174").rstrip("/")
OUT = Path(os.getenv("E2E_OUTPUT_DIR", ROOT / "docs/validacao/ortomapas_conclusao/etapa-02"))
DATA = ROOT / "data"


def delete_test_users(emails: list[str], project_id: int | None, project_name: str) -> None:
    """Use the configured PostgreSQL helper; delete only uniquely named test rows."""
    cleanup = r'''
import json, os
from backend.database.connection import get_connection
emails=json.loads(os.environ["PHASE2_TEST_EMAILS"])
project_id=os.environ.get("PHASE2_TEST_PROJECT_ID")
project_name=os.environ["PHASE2_TEST_PROJECT_NAME"]
with get_connection() as conn:
    cur=conn.cursor()
    if project_id:
        cur.execute("DELETE FROM projetos WHERE id=%s AND nome=%s", (int(project_id), project_name))
    cur.execute("DELETE FROM usuarios WHERE email = ANY(%s)", (emails,))
    conn.commit()
    print("cleanup_complete")
'''
    env = os.environ.copy()
    env["PHASE2_TEST_EMAILS"] = json.dumps(emails)
    env["PHASE2_TEST_PROJECT_ID"] = str(project_id or "")
    env["PHASE2_TEST_PROJECT_NAME"] = project_name
    subprocess.run([str(ROOT / ".conda-env/bin/python"), "-c", cleanup], cwd=ROOT, env=env, check=True, capture_output=True, text=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    suffix = secrets.token_hex(5)
    owner_email = f"phase2-owner-{suffix}@example.test"
    reader_email = f"phase2-reader-{suffix}@example.test"
    password = secrets.token_urlsafe(24)
    project_name = f"Validação isolamento Fase 2 {suffix}"
    relative_file = ""
    private_file: Path | None = None

    result = {
        "phase": "2/8",
        "llm_calls": 0,
        "credentials_written_to_report": False,
        "project_name": project_name,
        "checks": [],
        "screenshots": [],
    }
    owner_id = reader_id = project_id = flight_id = ortho_id = None
    test_emails: list[str] = []
    failed = False

    with sync_playwright() as playwright:
        api = playwright.request.new_context()
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=os.getenv("CHROME_PATH") or which("google-chrome") or which("chromium"),
            args=["--no-sandbox"],
        )
        try:
            for email, name, profile in (
                (owner_email, "Conta temporária proprietária", "pesquisador"),
                (reader_email, "Conta temporária leitora", "leitor"),
            ):
                response = api.post(f"{API}/auth/register", data={"email": email, "nome": name, "senha": password, "perfil": profile})
                assert response.status == 201, f"Cadastro de conta temporária falhou: HTTP {response.status}"
                user_id = response.json()["id"]
                if profile == "pesquisador":
                    owner_id = user_id
                else:
                    reader_id = user_id
                test_emails.append(email)

            def login(email: str) -> str:
                response = api.post(f"{API}/auth/login", data={"email": email, "senha": password})
                assert response.status == 200, f"Login temporário falhou: HTTP {response.status}"
                return response.json()["access_token"]

            owner_token = login(owner_email)
            reader_token = login(reader_email)
            owner_headers = {"Authorization": f"Bearer {owner_token}"}
            reader_headers = {"Authorization": f"Bearer {reader_token}"}

            owner_context = browser.new_context(viewport={"width": 1440, "height": 1000})
            owner_page = owner_context.new_page()
            owner_page.goto(WEB, wait_until="networkidle")
            owner_page.screenshot(path=str(OUT / "01_login.png"), full_page=True)
            result["screenshots"].append("01_login.png")
            owner_page.get_by_label("E-mail").fill(owner_email)
            owner_page.locator('input[type="password"]').fill(password)
            owner_page.get_by_role("button", name="Entrar").click()
            owner_page.locator(".app-layout").wait_for(state="visible", timeout=20000)
            owner_page.get_by_role("button", name="Novo").click()
            dialog = owner_page.get_by_role("dialog")
            dialog.get_by_placeholder("Nome").fill(project_name)
            dialog.locator("textarea").fill("Projeto temporário isolado para teste de autorização entre usuários")
            dialog.get_by_placeholder("Ex: Fazenda Norte").fill("Área de validação")
            owner_page.screenshot(path=str(OUT / "02_projeto_novo_preenchido.png"), full_page=True)
            result["screenshots"].append("02_projeto_novo_preenchido.png")
            with owner_page.expect_response(lambda response: response.url.endswith("/api/projetos") and response.request.method == "POST") as project_response:
                dialog.get_by_role("button", name="Criar").click()
            created_project = project_response.value
            assert created_project.status == 201, f"Criação de projeto pela UI falhou: HTTP {created_project.status}"
            project_id = int(created_project.json()["id"])
            relative_file = f"analises/projetos/{project_id}/validacao_fase2_{suffix}/arquivo_privado.txt"
            private_file = DATA / relative_file
            private_file.parent.mkdir(parents=True, exist_ok=True)
            private_file.write_text("arquivo temporario para teste de autorização\n", encoding="utf-8")
            owner_page.get_by_text(project_name, exact=True).wait_for(state="visible", timeout=20000)
            dialog.wait_for(state="hidden", timeout=20000)
            owner_page.screenshot(path=str(OUT / "03_projeto_do_proprietario.png"), full_page=True)
            result["screenshots"].append("03_projeto_do_proprietario.png")
            result["checks"].append({"id": "P2-UI-01", "expected": "novo projeto visível após criação pela UI", "observed": "projeto criado via POST 201 e exibido na lista", "status": "passed"})

            owner_project = api.get(f"{API}/projetos/{project_id}", headers=owner_headers)
            assert owner_project.status == 200
            owner_members = api.get(f"{API}/projetos/{project_id}/usuarios", headers=owner_headers)
            assert owner_members.status == 200
            assert any(row["id"] == owner_id and row["papel"] == "proprietario" for row in owner_members.json()["usuarios"])
            result["checks"].append({"id": "P2-DB-01", "expected": "proprietário ligado ao projeto", "observed": "API confirma papel proprietario para a conta criadora", "status": "passed"})

            flight_response = api.post(f"{API}/voos", headers=owner_headers, data={"projeto_id": project_id, "data_voo": date.today().isoformat(), "observacoes": "voo descartável de teste de autorização"})
            assert flight_response.status == 201, f"Criação de voo de teste falhou: HTTP {flight_response.status}"
            flight_id = int(flight_response.json()["id"])
            ortho_response = api.post(f"{API}/ortomapas", headers=owner_headers, data={"projeto_id": project_id, "voo_id": flight_id, "nome": "Produto privado de validação", "tipo": "ortomosaico", "formato": "TXT-fixture", "caminho_arquivo": relative_file, "status": "disponivel"})
            assert ortho_response.status == 201, f"Criação de metadado de teste falhou: HTTP {ortho_response.status}"
            ortho_id = int(ortho_response.json()["id"])

            owner_flights = api.get(f"{API}/voos", headers=owner_headers)
            assert owner_flights.status == 200 and any(row["id"] == flight_id for row in owner_flights.json()["voos"])
            owner_access = api.post(f"{API}/media/access", headers=owner_headers, data={"path": relative_file})
            assert owner_access.status == 200, f"Proprietário não obteve acesso ao próprio arquivo: HTTP {owner_access.status}"
            media_url = API.removesuffix("/api") + owner_access.json()["url"]
            owner_file = api.get(media_url)
            assert owner_file.status == 200 and "arquivo temporario" in owner_file.text()
            result["checks"].append({"id": "P2-OWNER-01", "expected": "proprietário lê projeto, voo, produto e arquivo próprio", "observed": "GETs autorizados retornam 200 e arquivo de fixture correspondente", "status": "passed"})

            reader_context = browser.new_context(viewport={"width": 1440, "height": 1000})
            reader_page = reader_context.new_page()
            reader_page.goto(WEB, wait_until="networkidle")
            reader_page.get_by_label("E-mail").fill(reader_email)
            reader_page.locator('input[type="password"]').fill(password)
            reader_page.get_by_role("button", name="Entrar").click()
            reader_page.locator(".app-layout").wait_for(state="visible", timeout=20000)
            reader_page.get_by_text("Nenhum projeto encontrado", exact=True).wait_for(state="visible", timeout=20000)
            reader_page.screenshot(path=str(OUT / "04_lista_vazia_segundo_usuario.png"), full_page=True)
            result["screenshots"].append("04_lista_vazia_segundo_usuario.png")

            reader_projects = api.get(f"{API}/projetos", headers=reader_headers)
            assert reader_projects.status == 200 and all(row["id"] != project_id for row in reader_projects.json()["projetos"])
            assert api.get(f"{API}/projetos/{project_id}", headers=reader_headers).status == 403
            assert api.get(f"{API}/projetos/{project_id}/ortomapas", headers=reader_headers).status == 403
            assert api.get(f"{API}/ortomapas/{ortho_id}", headers=reader_headers).status == 403
            assert api.get(f"{API}/voos/{flight_id}", headers=reader_headers).status == 403
            assert api.get(f"{API}/ortomapas/{ortho_id}/tile-access", headers=reader_headers).status == 403
            denied_file = api.post(f"{API}/media/access", headers=reader_headers, data={"path": relative_file})
            assert denied_file.status == 403
            denied_update = api.put(f"{API}/projetos/{project_id}", headers=reader_headers, data={"nome": "alteração indevida"})
            assert denied_update.status == 403

            reader_flights = api.get(f"{API}/voos", headers=reader_headers)
            assert reader_flights.status == 200 and all(row["id"] != flight_id for row in reader_flights.json()["voos"])
            result["checks"].append({"id": "P2-ISOLATION-01", "expected": "segundo usuário não lista nem lê recursos privados", "observed": "projeto/voo/produto/arquivo/tile negados ou omitidos; escrita negada", "http": {"project": 403, "project_ortomaps": 403, "ortomapa": 403, "flight": 403, "tile_ticket": 403, "file_access": denied_file.status, "update": denied_update.status}, "status": "passed"})

            # Regression guard for readers lacking project membership.
            denied_members = api.get(f"{API}/projetos/{project_id}/usuarios", headers=reader_headers)
            result["checks"].append({"id": "P2-REG-01", "expected": "403 ao listar membros de projeto sem associação", "observed_http": denied_members.status, "status": "passed" if denied_members.status == 403 else "failed"})
            assert denied_members.status == 403, f"Vazamento de membros: HTTP {denied_members.status} para leitor não associado"

            result["status"] = "passed"
            owner_context.close()
            reader_context.close()
        except Exception as exc:
            failed = True
            result["status"] = "failed"
            result["error"] = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            if project_id and owner_id:
                try:
                    response = api.delete(f"{API}/projetos/{project_id}", headers={"Authorization": f"Bearer {login(owner_email)}"})
                    result["project_deleted_via_api"] = response.status == 200
                except Exception:
                    result["project_deleted_via_api"] = False
            try:
                delete_test_users(test_emails, project_id, project_name)
                result["temporary_database_records_removed"] = True
            except Exception as cleanup_error:
                result["temporary_database_records_removed"] = False
                result["cleanup_error"] = str(cleanup_error)
            if private_file is not None:
                shutil.rmtree(private_file.parent, ignore_errors=True)
            result["temporary_file_removed"] = private_file is None or not private_file.exists()
            (OUT / "playwright_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            browser.close()
            api.dispose()

    return 1 if failed or result.get("temporary_database_records_removed") is not True else 0


if __name__ == "__main__":
    raise SystemExit(main())
