"""Explicit, persistent Playwright run using the real Aukerman photo set.

Run only with ODM_REAL_RUN=1. It creates a flight and a real NodeODM task in
the configured project; the resulting task/products are intentionally kept.
"""

import os
from datetime import date, datetime
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[3]
IMAGES = Path(os.getenv("ODM_REAL_IMAGES", ROOT / "data/odm_test/odm_data_aukerman-master/images"))
OUT = ROOT / "docs/validacao/odm_fase6_2026-10-16"
PROJECT_ID = int(os.getenv("ODM_REAL_PROJECT_ID", "62"))


def wait_for_basemap(page):
    page.wait_for_function("""() => [...document.querySelectorAll('img.leaflet-tile')]
      .filter(tile => tile.complete && tile.naturalWidth === 256).length >= 8""", timeout=30_000)


@pytest.mark.skipif(os.getenv("ODM_REAL_RUN") != "1", reason="Creates a persistent NodeODM task; set ODM_REAL_RUN=1 explicitly")
def test_real_odm_end_to_end():
    photos = sorted([*IMAGES.glob("*.JPG"), *IMAGES.glob("*.jpg"), *IMAGES.glob("*.jpeg")])
    assert len(photos) >= 3, f"Fotos nao encontradas em {IMAGES}"
    OUT.mkdir(parents=True, exist_ok=True)
    base_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176")
    project_name = os.getenv("ODM_REAL_PROJECT_NAME", "Validacao Fase 1 - Ortofoto real Aukerman")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        flight_name = f"NodeODM Aukerman Fase 6 {datetime.now().strftime('%H%M%S')}"
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        page.set_default_timeout(30_000)
        page.goto(base_url, wait_until="networkidle")
        page.locator("input[type=email]").fill(os.getenv("E2E_EMAIL", "phase1-1791391595@example.test"))
        page.locator("input[type=password]").fill(os.getenv("E2E_PASSWORD", "fase1-senha-segura"))
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.get_by_text(project_name, exact=True).first.click()
        page.locator(".workspace-sidebar-nav").get_by_text("Voos e ODM", exact=True).click()

        resume_task_id = os.getenv("ODM_REAL_RESUME_TASK_ID")
        if resume_task_id:
            jobs = page.evaluate("""async ({ projectId }) => {
              const token = localStorage.getItem('ortomapas_token')
              const response = await fetch(`/api/odm/processamentos?projeto_id=${projectId}`, {
                headers: { Authorization: `Bearer ${token}` }
              })
              if (!response.ok) throw new Error(await response.text())
              return (await response.json()).processamentos
            }""", {"projectId": PROJECT_ID})
            resumed = next((item for item in jobs if item["odm_task_id"].startswith(resume_task_id)), None)
            assert resumed, f"Task {resume_task_id} nao encontrada no projeto {PROJECT_ID}"
            processing_id = resumed["id"]
            task_id = resumed["odm_task_id"]
            wait_for_basemap(page)
            page.screenshot(path=str(OUT / "02_task_enviada.png"), full_page=True)
        else:
            page.get_by_role("button", name="Novo", exact=True).click()
            dialog = page.locator(".p-dialog").filter(has_text="Novo Voo")
            dialog.locator('input[type="date"]').fill(date.today().isoformat())
            dialog.get_by_placeholder("Ex: DJI Fly").fill(flight_name)
            dialog.get_by_placeholder("120").fill("120")
            dialog.locator('input[type="number"]').nth(1).fill(str(len(photos)))
            dialog.get_by_role("button", name="Criar", exact=True).click()
            row = page.locator(".voo-item").filter(has_text=flight_name)
            row.wait_for()

            row.get_by_role("button", name="Fotos", exact=True).click()
            page.locator('input[type="file"]').set_input_files([str(path) for path in photos])
            upload_dialog = page.locator(".p-dialog").filter(has_text="Processar fotos no ODM")
            upload_dialog.get_by_text(f"{len(photos)} foto(s)", exact=False).wait_for()
            page.screenshot(path=str(OUT / "01_fotos_selecionadas.png"), full_page=True)

            with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith("/odm/tasks"), timeout=600_000) as submission:
                upload_dialog.get_by_role("button", name="Iniciar processamento", exact=True).click()
            assert submission.value.status == 202, submission.value.text()
            submitted = submission.value.json()
            assert submitted["images_count"] == len(photos)
            assert submitted["geotagged_count"] >= 3
            processing_id = submitted["processamento_id"]
            task_id = submitted["task"]["uuid"]
            page.get_by_text("Processamento iniciado no NodeODM", exact=False).wait_for()
            upload_dialog.wait_for(state="hidden")
            page.locator(".p-dialog-mask").wait_for(state="hidden")
            page.locator(".task-row").filter(has_text=task_id[:8]).wait_for()
            wait_for_basemap(page)
            page.screenshot(path=str(OUT / "02_task_enviada.png"), full_page=True)

        page.set_default_timeout(6 * 60 * 60 * 1000)
        deadline = int(os.getenv("ODM_REAL_TIMEOUT_SECONDS", str(6 * 60 * 60)))
        elapsed = 0
        last_screenshot = bool(resume_task_id)
        while elapsed < deadline:
            page.wait_for_timeout(15_000)
            elapsed += 15
            jobs = page.evaluate("""async ({ projectId }) => {
              const token = localStorage.getItem('ortomapas_token')
              const response = await fetch(`/api/odm/processamentos?projeto_id=${projectId}`, {
                headers: { Authorization: `Bearer ${token}` }
              })
              if (!response.ok) throw new Error(await response.text())
              return (await response.json()).processamentos
            }""", {"projectId": PROJECT_ID})
            job = next((item for item in jobs if item["id"] == processing_id), None)
            assert job, f"Processamento {processing_id} sumiu do catalogo"
            options = job.get("parametros") or []
            disabled = {"fast-orthophoto", "skip-3dmodel", "resize-to"}
            assert not disabled.intersection(option.get("name") for option in options), f"Parametros ODM inesperados: {options}"
            if not last_screenshot:
                page.screenshot(path=str(OUT / "03_processando.png"), full_page=True)
                last_screenshot = True
            if job["status"] == "erro":
                page.screenshot(path=str(OUT / "erro_odm.png"), full_page=True)
                pytest.fail(f"NodeODM falhou: {job.get('erro') or job.get('etapa')}")
            if job["status"] == "concluido":
                break
        else:
            pytest.fail(f"NodeODM nao concluiu em {deadline}s; task={task_id}")

        page.locator(".task-row").filter(has_text=task_id[:8]).get_by_text("Concluído", exact=True).wait_for()
        page.screenshot(path=str(OUT / "04_task_concluida.png"), full_page=True)
        task_row = page.locator(".task-row").filter(has_text=task_id[:8])
        if task_row.get_by_role("button", name="Importar produtos", exact=True).count():
            with page.expect_response(lambda r: r.request.method == "POST" and r.url.endswith(f"/odm/processamentos/{processing_id}/importar"), timeout=6 * 60 * 60 * 1000) as importing:
                task_row.get_by_role("button", name="Importar produtos", exact=True).click()
            assert importing.value.status == 200, importing.value.text()
            imported = importing.value.json()
        else:
            imported = page.evaluate("""async ({ projectId, processingId }) => {
              const token = localStorage.getItem('ortomapas_token')
              const response = await fetch(`/api/odm/produtos?projeto_id=${projectId}`, {
                headers: { Authorization: `Bearer ${token}` }
              })
              if (!response.ok) throw new Error(await response.text())
              return { produtos: (await response.json()).produtos.filter(p => p.processamento_id === processingId) }
            }""", {"projectId": PROJECT_ID, "processingId": processing_id})
        assert any(product["tipo"] == "ortomosaico" for product in imported["produtos"])
        task_row.get_by_role("button", name="Abrir ortofoto", exact=True).wait_for()
        page.screenshot(path=str(OUT / "05_produtos_importados.png"), full_page=True)

        task_row.locator('button[title="Avaliar qualidade"]').click()
        task_row.get_by_text("Qualidade:", exact=False).wait_for()
        quality_result = page.evaluate("""async ({ processingId }) => {
          const token = localStorage.getItem('ortomapas_token')
          const response = await fetch(`/api/odm/processamentos/${processingId}/qualidade`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          if (!response.ok) throw new Error(await response.text())
          return response.json()
        }""", {"processingId": processing_id})
        assert quality_result["metricas"]["pontos_laz"] >= 100_000, quality_result
        assert quality_result["score"] == 100, quality_result
        page.screenshot(path=str(OUT / "08_avaliacao_qualidade.png"), full_page=True)

        before_count = len(imported["produtos"])
        duplicate_import = page.evaluate("""async ({ processingId }) => {
          const token = localStorage.getItem('ortomapas_token')
          const response = await fetch(`/api/odm/processamentos/${processingId}/importar`, {
            method: 'POST', headers: { Authorization: `Bearer ${token}` }
          })
          return { status: response.status, body: await response.json() }
        }""", {"processingId": processing_id})
        assert duplicate_import["status"] == 200, duplicate_import
        assert len(duplicate_import["body"]["produtos"]) == before_count, duplicate_import

        point_cloud_button = task_row.get_by_role("button", name="Abrir 3D", exact=True)
        if point_cloud_button.count():
            point_cloud_button.click()
            page.locator(".viewer-shell").wait_for(timeout=30_000)
            page.wait_for_timeout(2000)
            page.screenshot(path=str(OUT / "09_nuvem_laz_3d.png"), full_page=True)
            page.locator('.viewer-shell button[title="Fechar"]').click()

        task_row.get_by_role("button", name="Abrir ortofoto", exact=True).click()
        catalog = page.evaluate("""async ({ projectId, processingId }) => {
          const token = localStorage.getItem('ortomapas_token')
          const response = await fetch(`/api/odm/produtos?projeto_id=${projectId}`, {
            headers: { Authorization: `Bearer ${token}` }
          })
          if (!response.ok) throw new Error(await response.text())
          return (await response.json()).produtos.filter(p => p.processamento_id === processingId)
        }""", {"projectId": PROJECT_ID, "processingId": processing_id})
        ortho = next(item for item in catalog if item["tipo"] == "ortomosaico")
        ortho_id = ortho["ortomapa_id"]
        page.wait_for_function("""id => {
          const tiles = [...document.querySelectorAll('img.leaflet-tile')]
            .filter(tile => tile.src.includes(`/api/ortomapas/${id}/tile/`))
          return tiles.length >= 4 && tiles.every(tile => tile.complete && tile.naturalWidth === 256)
        }""", arg=ortho_id, timeout=120_000)
        page.screenshot(path=str(OUT / "06_ortofoto_importada.png"), full_page=True)

        dsm_button = task_row.get_by_role("button", name="DSM 3D", exact=True)
        if dsm_button.count():
            dsm_button.click()
            page.locator(".surface-view").wait_for(timeout=30_000)
            page.wait_for_timeout(3000)
            page.screenshot(path=str(OUT / "07_superficie_dsm_3d.png"), full_page=True)
        context.close()
        browser.close()
