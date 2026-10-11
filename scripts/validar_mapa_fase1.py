"""Capture actual map interactions and compare XYZ tiles with independent reprojection."""

import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path

import numpy as np
import rasterio
import requests
from PIL import Image
from playwright.sync_api import sync_playwright
from rasterio.transform import from_bounds
from rasterio.warp import reproject, transform_bounds, Resampling

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/validacao/mapa_fase1_2026-10-10"
API = os.getenv("VALIDATION_API", "http://127.0.0.1:5018/api")
UI = os.getenv("VALIDATION_UI", "http://127.0.0.1:5302")
NAME = "Validacao Fase 1 - Ortofoto real Aukerman"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["antes", "depois"])
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    result_path = OUT / f"resultado_{args.stage}.json"
    if args.stage == "antes" and result_path.exists():
        parser.error("A evidencia anterior a correcao esta preservada; use outro diretorio para nova linha de base.")
    result_path.write_text(json.dumps({"stage": args.stage, "status": "running", "accepted": False}), encoding="utf-8")
    email = os.getenv("E2E_EMAIL", "phase1-1791391595@example.test")
    password = os.getenv("E2E_PASSWORD", "fase1-senha-segura")
    session = requests.Session()
    login = session.post(API + "/auth/login", json={"email": email, "senha": password})
    login.raise_for_status()
    session.headers["Authorization"] = "Bearer " + login.json()["access_token"]
    response = session.get(API + "/projetos")
    response.raise_for_status()
    project = next((p for p in response.json()["projetos"] if p["nome"] == NAME), None)
    source = ROOT / "data/ortomapas/odm_2_ortomosaico.tif"
    with rasterio.open(source) as ds:
        west, south, east, north = transform_bounds(ds.crs, "EPSG:4326", *ds.bounds)
        if project is None:
            response = session.post(API + "/projetos", json={"nome": NAME, "descricao": "Validacao visual com produtos ODM reais; nao e Guarajuba.", "bbox_oeste": west, "bbox_sul": south, "bbox_leste": east, "bbox_norte": north, "centro_lat": (south + north) / 2, "centro_lon": (west + east) / 2})
            response.raise_for_status()
            project = response.json()
        response = session.get(API + "/ortomapas", params={"projeto_id": project["id"]})
        response.raise_for_status()
        orthos = response.json()["ortomapas"]
        ortho = next((o for o in orthos if o["nome"] == "Aukerman - ortofoto ODM real"), None)
        if ortho is None:
            response = session.post(API + "/voos", json={"projeto_id": project["id"], "data_voo": "2026-10-10", "observacoes": "Registro de validacao: reutilizacao de produto ODM real existente, nao novo voo."})
            response.raise_for_status()
            flight = response.json()
            response = session.post(API + "/ortomapas", json={"projeto_id": project["id"], "voo_id": flight["id"], "nome": "Aukerman - ortofoto ODM real", "tipo": "ortomosaico", "caminho_arquivo": str(source.relative_to(ROOT / "data")), "status": "disponivel", "sistema_coordenadas": str(ds.crs), "resolucao_cm": abs(ds.res[0]) * 100, "largura_px": ds.width, "altura_px": ds.height, "bbox_oeste": west, "bbox_sul": south, "bbox_leste": east, "bbox_norte": north})
            response.raise_for_status()
            ortho = response.json()
        manifest = {"project_id": project["id"], "ortomapa_id": ortho["id"], "file": str(source.relative_to(ROOT)), "sha256": hashlib.file_digest(source.open("rb"), "sha256").hexdigest(), "crs": str(ds.crs), "size": [ds.width, ds.height], "bands": ds.count, "resolution_m": ds.res, "bounds_wgs84": [west, south, east, north], "provenance": "Produto ODM existente, dados Aukerman; nao sintetico; nao corresponde a Guarajuba."}
        (OUT / "dados.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        # A tile crossing the western edge reveals stretching and missing alpha.
        z = 17
        n = 2 ** z
        x = int((west + 180) / 360 * n)
        y = int((1 - math.asinh(math.tan(math.radians((south + north) / 2))) / math.pi) / 2 * n)
        span = 40075016.68557849 / n
        left, top = -20037508.342789244 + x * span, 20037508.342789244 - y * span
        dst_transform = from_bounds(left, top - span, left + span, top, 256, 256)
        expected = np.zeros((4, 256, 256), dtype=np.uint8)
        for band in range(1, 5):
            reproject(rasterio.band(ds, band), expected[band - 1], src_transform=ds.transform, src_crs=ds.crs, dst_transform=dst_transform, dst_crs="EPSG:3857", resampling=Resampling.bilinear, src_alpha=4 if band < 4 else 0)
    expected = expected.transpose(1, 2, 0)
    Image.fromarray(expected).save(OUT / "tile_esperado.png")
    response = session.get(f"{API}/ortomapas/{ortho['id']}/tile/{z}/{x}/{y}.png")
    response.raise_for_status()
    actual = np.asarray(Image.open(io.BytesIO(response.content)).convert("RGBA"))
    Image.fromarray(actual).save(OUT / f"tile_{args.stage}.png")
    mask_expected = expected[:, :, 3] > 0
    mask_actual = actual[:, :, 3] > 0
    union = np.logical_or(mask_expected, mask_actual).sum()
    intersection = np.logical_and(mask_expected, mask_actual).sum()
    valid = mask_expected & mask_actual
    metrics = {"stage": args.stage, "tile": [z, x, y], "mask_iou": float(intersection / union), "expected_coverage": float(mask_expected.mean()), "actual_coverage": float(mask_actual.mean()), "rgb_mean_absolute_error": float(np.abs(actual[:, :, :3].astype(float) - expected[:, :, :3].astype(float))[valid].mean()), "screens": [], "page_errors": [], "failed_tiles": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda err: metrics["page_errors"].append(str(err)))
        page.on("response", lambda r: metrics["failed_tiles"].append({"url": r.url, "status": r.status}) if "/tile/" in r.url and r.status >= 400 else None)
        page.goto(UI, wait_until="networkidle")
        page.locator("input[type=email]").fill(email)
        page.locator("input[type=password]").fill(password)
        page.get_by_role("button", name="Entrar", exact=True).click()
        page.locator(".project-selector").click()
        page.get_by_role("option", name=NAME, exact=True).click()
        card = page.locator(".ortomapa-card").filter(has_text="Aukerman - ortofoto ODM real")
        card.wait_for()
        card.get_by_title("Visibilidade", exact=True).click()
        page.wait_for_function("""() => { const images = [...document.querySelectorAll('.leaflet-tile-pane img')].filter(i => i.src.includes('/api/ortomapas/')); return images.length > 0 && images.every(i => i.complete && i.naturalWidth === 256) }""", timeout=60000)
        page.locator(".leaflet-tile-loading").wait_for(state="detached", timeout=60000)
        def capture(label):
            page.wait_for_function("""() => [...document.querySelectorAll('.leaflet-tile-pane img')].every(i => i.complete && getComputedStyle(i).opacity === '1')""", timeout=60000)
            filename = f"{args.stage}_{label}.png"
            page.screenshot(path=str(OUT / filename))
            metrics["screens"].append(filename)
        capture("01_ortofoto_ativada")
        metrics["raster_pixels_loaded"] = page.evaluate("""() => [...document.querySelectorAll('.leaflet-tile-pane img')].filter(i => i.src.includes('/api/ortomapas/')).reduce((count, image) => { const c = document.createElement('canvas'); c.width = c.height = 256; const ctx = c.getContext('2d'); ctx.drawImage(image, 0, 0); const data = ctx.getImageData(0, 0, 256, 256).data; for(let i = 3; i < data.length; i += 4) if(data[i] > 0) count++; return count }, 0)""")
        if args.stage == "depois":
            assert metrics["raster_pixels_loaded"] > 1000, "Loaded tiles are transparent; ortho not demonstrated"
        slider = page.locator(".layer-controls input[type=range]")
        slider.fill("0.5")
        capture("02_opacidade_50")
        assert page.locator('.leaflet-tile-pane .leaflet-layer').evaluate_all("els => els.some(e => Math.abs(parseFloat(e.style.opacity) - 0.5) < 0.01)")
        card.get_by_title("Visibilidade", exact=True).click()
        page.wait_for_function("!document.querySelector('.leaflet-tile-pane img[src*=\"/api/ortomapas/\"]')")
        capture("03_camada_oculta")
        card.get_by_title("Visibilidade", exact=True).click()
        page.wait_for_function("""() => { const images = [...document.querySelectorAll('.leaflet-tile-pane img')].filter(i => i.src.includes('/api/ortomapas/')); return images.length > 0 && images.every(i => i.complete && i.naturalWidth === 256) }""")
        slider.fill("1")
        capture("04_camada_restaurada")
        if args.stage == "depois":
            # A second viewport exercises the same actions, not a static mobile mock.
            page.set_viewport_size({"width": 1024, "height": 768})
            page.locator(".sidebar-toggle").first.click()
            page.locator(".sidebar-right .sidebar-toggle").click() if page.locator(".sidebar-right .sidebar-toggle").count() else None
            page.wait_for_function("""() => document.querySelector('.sidebar-left').getBoundingClientRect().width <= 57 && document.querySelector('.sidebar-right').getBoundingClientRect().width <= 33""")
            page.wait_for_function("""() => [...document.querySelectorAll('.leaflet-tile-pane img')].every(i => i.complete && getComputedStyle(i).opacity === '1')""")
            capture("05_tablet_barra_recolhida")
        browser.close()
    metrics["status"] = "completed"
    metrics["accepted"] = metrics["mask_iou"] >= 0.99 and metrics["rgb_mean_absolute_error"] <= 1 and metrics["raster_pixels_loaded"] > 1000 and not metrics["page_errors"] and not metrics["failed_tiles"]
    result_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    if args.stage == "depois" and not metrics["accepted"]:
        raise SystemExit("Visual validation failed")


if __name__ == "__main__":
    main()
