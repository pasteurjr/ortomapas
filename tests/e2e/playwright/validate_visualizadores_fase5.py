"""Read-only Playwright validation of real ODM 3D products in project 64."""
from __future__ import annotations

import json
import os
import struct
import sys
import io
from pathlib import Path

import laspy
import numpy as np
import rasterio
import requests
from PIL import Image
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    # Playwright is installed in the user's automation Conda environment; keep
    # the GIS application's separate Conda environment free of extra packages.
    automation_site = Path.home() / "anaconda3/envs/copa2026/lib/python3.11/site-packages"
    if automation_site.is_dir():
        sys.path.insert(0, str(automation_site))
    from playwright.sync_api import sync_playwright

from backend.database.connection import get_connection
from backend.routers.auth import _token, active_user

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.getenv("ODM_PHASE5_OUT", ROOT / "docs/validacao/ortomapas_conclusao/etapa-05"))
UI = os.getenv("FRONTEND_URL", "http://127.0.0.1:5176")
API = os.getenv("API_URL", "http://127.0.0.1:8888/api")
PROJECT_ID = int(os.getenv("ODM_PHASE5_PROJECT_ID", "64"))
PROCESSING_ID = int(os.getenv("ODM_PHASE5_PROCESSING_ID", "15"))


def glb_declared_mesh_stats(path: Path) -> dict:
    blob = path.read_bytes()
    magic, version, total_bytes = struct.unpack_from("<4sII", blob, 0)
    if magic != b"glTF" or version != 2 or total_bytes != len(blob):
        raise AssertionError("GLB inválido: cabeçalho/marcador não corresponde ao arquivo")
    chunk_bytes, chunk_type = struct.unpack_from("<I4s", blob, 12)
    if chunk_type != b"JSON":
        raise AssertionError("GLB sem primeiro chunk JSON")
    document = json.loads(blob[20:20 + chunk_bytes].decode("utf-8").rstrip("\0 "))
    triangles = 0
    material_ids = set()
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4:
                continue
            accessors = document.get("accessors", [])
            count = (accessors[primitive["indices"]]["count"] if "indices" in primitive
                     else accessors[primitive["attributes"]["POSITION"]]["count"])
            triangles += count // 3
            if "material" in primitive:
                material_ids.add(primitive["material"])
    return {"bytes": len(blob), "triangles": triangles,
            "materials": len(material_ids), "meshes": len(document.get("meshes", [])),
            "extensions": document.get("extensionsUsed", [])}


def raster_stats(path: Path) -> dict:
    with rasterio.open(path) as raster:
        values = raster.read(1, masked=True)
        return {
            "crs": raster.crs.to_string(), "width": raster.width, "height": raster.height,
            "bounds": [round(value, 3) for value in raster.bounds],
            "resolution_m": [round(value, 3) for value in raster.res],
            "valid_pixels": int(values.count()), "min_m": round(float(values.min()), 3),
            "max_m": round(float(values.max()), 3),
        }


def orbit_and_zoom(page, canvas) -> int:
    """Assert mouse drag and wheel produce a visible WebGL view change."""
    before = np.asarray(Image.open(io.BytesIO(canvas.screenshot())).convert("RGB"))
    box = canvas.bounding_box()
    if not box:
        raise AssertionError("Canvas WebGL sem caixa visível")
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 70, y + 45, steps=8)
    page.mouse.up()
    page.mouse.wheel(0, -180)
    page.wait_for_timeout(350)
    after = np.asarray(Image.open(io.BytesIO(canvas.screenshot())).convert("RGB"))
    changed = int(np.count_nonzero(np.any(before != after, axis=2)))
    if changed < 100:
        raise AssertionError(f"Rotação/zoom não alteraram a visualização ({changed} pixels)")
    return changed


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuarios WHERE perfil='admin' AND ativo=true ORDER BY id LIMIT 1")
        admin = cursor.fetchone()
        if not admin:
            raise AssertionError("Não há usuário administrativo ativo para a sessão E2E local")
        user = active_user(admin["id"])
        cursor.execute("""SELECT id,tipo,caminho,formato,crs FROM produtos_processamento
                          WHERE processamento_id=%s ORDER BY id""", (PROCESSING_ID,))
        products = cursor.fetchall()
    token = _token(user)  # Local test session only; never written to the report.
    product_by_type = {row["tipo"]: row for row in products}
    required = {"dsm", "dtm", "modelo_3d", "nuvem_pontos"}
    if not required.issubset(product_by_type):
        raise AssertionError(f"Produtos ausentes no processamento: {sorted(required - product_by_type.keys())}")
    paths = {kind: ROOT / "data" / product_by_type[kind]["caminho"]
             for kind in required}
    for kind, path in paths.items():
        if not path.is_file():
            raise AssertionError(f"Arquivo real ausente para {kind}: {path}")

    headers = {"Authorization": f"Bearer {token}"}
    products_response = requests.get(f"{API}/odm/produtos", params={"projeto_id": PROJECT_ID}, headers=headers, timeout=30)
    products_response.raise_for_status()
    listed = [item for item in products_response.json()["produtos"]
              if item["processamento_id"] == PROCESSING_ID]
    if {item["tipo"] for item in listed} < required:
        raise AssertionError("Catálogo HTTP não lista todos os produtos do processamento")

    references = {
        "DSM": raster_stats(paths["dsm"]), "DTM": raster_stats(paths["dtm"]),
        "LAZ": {}, "GLB": glb_declared_mesh_stats(paths["modelo_3d"]),
    }
    with laspy.open(paths["nuvem_pontos"]) as cloud:
        header = cloud.header
        crs = header.parse_crs()
        references["LAZ"] = {"points": header.point_count,
            "crs": crs.to_string() if crs else None,
            "bounds_min": [round(float(v), 3) for v in header.mins],
            "bounds_max": [round(float(v), 3) for v in header.maxs],
            "units": "m"}
    if references["LAZ"]["crs"] != "EPSG:32617":
        raise AssertionError(f"CRS LAZ inesperado: {references['LAZ']['crs']}")

    # Independently read the same API grids/samples consumed by the WebGL viewers.
    surfaces = {}
    for kind in ("DSM", "DTM"):
        product_id = product_by_type[kind.lower()]["id"]
        response = requests.get(f"{API}/odm/produtos/{product_id}/surface",
                                params={"max_size": 128}, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        surfaces[kind] = {key: data[key] for key in ("width", "height", "min", "max", "metric_crs", "units", "bounds")}
        surfaces[kind]["triangles_max"] = (data["width"] - 1) * (data["height"] - 1) * 2
        if data["metric_crs"] != references[kind]["crs"] or data["units"] != "m":
            raise AssertionError(f"Unidade/CRS da grade {kind} diverge do raster original")
        if any(abs(actual - expected) > 0.01 for actual, expected in zip(data["bounds"], references[kind]["bounds"])):
            raise AssertionError(f"A extensão API {kind} diverge do arquivo raster original")
        if data["min"] < references[kind]["min_m"] - 1e-3 or data["max"] > references[kind]["max_m"] + 1e-3:
            raise AssertionError(f"Extremos da grade {kind} extrapolam os valores do raster original")

    cloud_product_id = product_by_type["nuvem_pontos"]["id"]
    cloud_response = requests.get(f"{API}/odm/produtos/{cloud_product_id}/points",
                                  params={"max_points": 120000}, headers=headers, timeout=120)
    cloud_response.raise_for_status()
    cloud_data = cloud_response.json()
    if cloud_data["units"] != "m" or cloud_data["source_crs"] != references["LAZ"]["crs"]:
        raise AssertionError("Unidades/CRS da amostra LAZ não correspondem ao cabeçalho")
    if cloud_data["total"] != references["LAZ"]["points"] or cloud_data["sampled"] > 120000:
        raise AssertionError("Contagem total/amostra da API LAZ difere dos limites requisitados")

    result = {"status": "passed", "project_id": PROJECT_ID, "processing_id": PROCESSING_ID,
              "dataset_origin": "Conjunto público ODM Aukerman; não representa voo/drone de Guarajuba.",
              "read_only": True, "products": {kind: {"id": product_by_type[kind.lower()]["id"],
                  "format": product_by_type[kind.lower()]["formato"], "bytes": path.stat().st_size}
                  for kind, path in paths.items()}, "source_reference": references,
              "surface_api": surfaces,
              "cloud_api": {"total": cloud_data["total"], "sampled": cloud_data["sampled"],
                  "units": cloud_data["units"], "source_crs": cloud_data["source_crs"],
                  "bounds": cloud_data["bounds"]}, "screenshots": [], "browser_errors": []}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True,
            executable_path=os.getenv("CHROME_PATH", "/usr/bin/google-chrome"), args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1680, "height": 1050}, accept_downloads=True)
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.add_init_script(f"localStorage.setItem('ortomapas_token',{json.dumps(token)})")
        page.goto(UI, wait_until="domcontentloaded")
        page.locator(".workspace-sidebar-nav").wait_for(timeout=30000)
        page.locator(".project-item").filter(has_text="Aceite NodeODM Aukerman 20261105-144156").click()
        page.locator(".workspace-sidebar-nav").get_by_text("Voos e ODM", exact=True).click()
        task_id = None
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT odm_task_id FROM processamentos_odm WHERE id=%s", (PROCESSING_ID,))
            task_id = cursor.fetchone()["odm_task_id"]
        task = page.locator(".task-row").filter(has_text=task_id[:8])
        task.wait_for(timeout=30000)

        def capture(name: str, description: str) -> None:
            path = OUT / f"{name}.png"
            page.screenshot(path=str(path), full_page=True, animations="disabled")
            result["screenshots"].append({"file": path.name, "description": description})

        capture("01_catalogo_produtos_3d", "A tarefa ODM real concluída expõe ações separadas para modelo GLB, DSM, DTM e nuvem LAZ.")

        task.get_by_role("button", name="Modelo texturizado 3D", exact=True).click()
        model = page.locator(".model-view")
        model.wait_for(timeout=30000)
        page.locator(".model-view .canvas-host canvas").wait_for(timeout=30000)
        page.wait_for_function("""() => {
          const host=document.querySelector('.model-view .canvas-host');
          return host?.dataset.modelState === 'loaded' && !!document.querySelector('.model-view footer');
        }""", timeout=120000)
        model_footer = page.locator(".model-view footer").inner_text()
        if f"{references['GLB']['triangles']:,}".replace(",", ".") not in model_footer:
            raise AssertionError(f"Contagem de triângulos GLB no viewer diverge: {model_footer}")
        if f"{references['GLB']['materials']} materiais" not in model_footer:
            raise AssertionError(f"Contagem de materiais GLB no viewer diverge: {model_footer}")
        model_change = orbit_and_zoom(page, page.locator(".model-view .canvas-host canvas"))
        capture("02_modelo_texturizado_glb", f"GLB {references['GLB']['triangles']} triângulos e {references['GLB']['materials']} materiais/texturas; carregamento WebGL concluído.")
        result["GLB_viewer"] = {"status": "passed", "footer": model_footer,
                                "orbit_zoom_changed_pixels": model_change}
        page.locator('.model-view button[title="Fechar"]').click()
        model.wait_for(state="detached")

        for kind, button_name in (("DSM", "DSM 3D"), ("DTM", "DTM 3D")):
            task.get_by_role("button", name=button_name, exact=True).click()
            surface = page.locator(".surface-view")
            surface.wait_for(timeout=30000)
            page.locator(".surface-view .host canvas").wait_for(timeout=30000)
            page.wait_for_function("""() => {
              const el=document.querySelector('.surface-view');
              return el && !el.querySelector('.overlay:not(.error)') && !!el.querySelector('footer');
            }""", timeout=90000)
            footer = page.locator(".surface-view footer").inner_text()
            expected_min = f"{surfaces[kind]['min']:.1f} m"
            expected_max = f"{surfaces[kind]['max']:.1f} m"
            if expected_min not in footer or expected_max not in footer:
                raise AssertionError(f"Legenda {kind} diverge da grade API: {footer}")
            slider = page.get_by_role("slider", name="Exagero vertical do terreno")
            slider.fill("2")
            if "Vertical 2x" not in page.locator(".surface-view footer").inner_text():
                raise AssertionError(f"Controle de exagero vertical {kind} não atualizou")
            page.locator('.surface-view button[title="Alternar wireframe"]').click()
            if page.locator('.surface-view button[title="Alternar wireframe"]').get_attribute("aria-pressed") != "true":
                raise AssertionError(f"Wireframe {kind} não alternou")
            page.locator('.surface-view button[title="Alternar wireframe"]').click()
            interaction_change = orbit_and_zoom(page, page.locator(".surface-view .host canvas"))
            page.locator('.surface-view button[title="Enquadrar"]').click()
            capture("03_dsm_superficie_3d" if kind == "DSM" else "04_dtm_terreno_3d",
                    f"{kind} real em malha 3D; legenda confrontada com grade API; CRS {surfaces[kind]['metric_crs']}; controle vertical 2x e wireframe verificados.")
            result[f"{kind}_viewer"] = {"status": "passed", "footer": page.locator(".surface-view footer").inner_text(),
                                        "orbit_zoom_changed_pixels": interaction_change}
            page.locator('.surface-view button[title="Fechar"]').click()
            surface.wait_for(state="detached")

        task.get_by_role("button", name="Abrir 3D", exact=True).click()
        cloud = page.locator(".viewer-shell")
        cloud.wait_for(timeout=30000)
        page.locator(".viewer-shell .canvas-host canvas").wait_for(timeout=30000)
        page.wait_for_function("""() => {
          const shell=document.querySelector('.viewer-shell');
          return shell && !shell.querySelector('.overlay') && shell.querySelector('.viewer-header')?.innerText.includes('pontos');
        }""", timeout=120000)
        cloud_header = page.locator(".viewer-shell .viewer-header").inner_text()
        if f"{references['LAZ']['points']:,}".replace(",", ".") not in cloud_header:
            raise AssertionError(f"Total LAZ visível diverge do cabeçalho do arquivo: {cloud_header}")
        point_sample = page.locator(".viewer-shell .stats").inner_text()
        if f"{cloud_data['sampled']:,}".replace(",", ".") not in point_sample:
            raise AssertionError(f"Contagem da amostra LAZ não aparece na UI: {point_sample}")
        page.locator('.viewer-shell button[title="Vista superior"]').click()
        page.locator('.viewer-shell button[title="Vista frontal"]').click()
        page.locator('.viewer-shell button[title="Vista lateral"]').click()
        cloud_change = orbit_and_zoom(page, page.locator(".viewer-shell .canvas-host canvas"))
        page.locator('.viewer-shell button[title="Enquadrar nuvem"]').click()
        cloud_canvas = page.locator(".viewer-shell .canvas-host canvas")
        cloud_box = cloud_canvas.bounding_box()
        page.get_by_role("button", name="Inspecionar ponto").click()
        inspected = False
        inspection_text = ""
        for y_fraction in (0.40, 0.46, 0.52, 0.58, 0.64):
            for x_fraction in (0.28, 0.36, 0.44, 0.52, 0.60, 0.68):
                page.mouse.click(cloud_box["x"] + cloud_box["width"] * x_fraction,
                                 cloud_box["y"] + cloud_box["height"] * y_fraction)
                result_panel = page.locator(".viewer-shell .point-result")
                if result_panel.count():
                    inspection_text = result_panel.inner_text()
                    inspected = True
                    break
            if inspected:
                break
        if not inspected:
            raise AssertionError("Não foi possível selecionar um ponto visível da nuvem")
        if "Z" not in inspection_text or "Intensidade" not in inspection_text:
            raise AssertionError(f"Painel de inspeção sem coordenadas/atributos: {inspection_text}")
        capture("05_nuvem_laz_3d", f"LAZ {references['LAZ']['points']} pontos totais, amostra de {cloud_data['sampled']} pontos, CRS métrico EPSG:32617. Inspeção: {inspection_text.replace(chr(10), ' — ')}")
        page.locator('.viewer-shell button[title="Tela cheia"]').click()
        page.wait_for_function("document.fullscreenElement?.classList.contains('viewer-shell')", timeout=5000)
        page.keyboard.press("Escape")
        page.wait_for_function("document.fullscreenElement === null", timeout=5000)
        cloud.wait_for(state="detached")
        result["LAZ_viewer"] = {"status": "passed", "header": cloud_header,
                                "controls": "vistas superior/frontal/lateral; enquadrar",
                                "orbit_zoom_changed_pixels": cloud_change,
                                "point_inspection": inspection_text,
                                "fullscreen": "abriu; Escape saiu da tela cheia e fechou o visualizador"}

        result["browser_errors"] = page_errors
        if page_errors:
            raise AssertionError(f"Erros JavaScript do navegador: {page_errors}")
        browser.close()

    (OUT / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
