"""NodeODM integration endpoints for importing and monitoring photo tasks."""

import json
import hashlib
import logging
import os
import re
import uuid
import zipfile
import shutil
import rasterio
import laspy
import numpy as np
from pyproj import Transformer
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query

from backend.config import DATA_DIR, NODEODM_URL
from backend.database.connection import get_connection
from backend.routers.auth import current_user, require_project_role

logger = logging.getLogger(__name__)
router = APIRouter()
ODM_UPLOADS_DIR = Path(DATA_DIR) / "odm_uploads"
ODM_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", Path(name or "image.jpg").name)


@router.post("/odm/tasks", status_code=202)
async def create_odm_task(
    images: List[UploadFile] = File(...),
    projeto_id: int = Form(...),
    voo_id: int = Form(...),
    name: str = Form("Ortomapas ODM"),
    options: Optional[str] = Form(None),
    user: dict = Depends(current_user),
):
    """Store flight photos and submit them asynchronously to NodeODM."""
    if not images:
        raise HTTPException(status_code=400, detail="Envie pelo menos uma imagem")
    require_project_role(projeto_id, user, {"proprietario", "editor"})
    allowed = {".jpg", ".jpeg", ".tif", ".tiff"}
    task_dir = ODM_UPLOADS_DIR / str(uuid.uuid4())
    task_dir.mkdir(parents=True)
    paths = []
    digests = {}
    try:
        for image in images:
            suffix = Path(image.filename or "").suffix.lower()
            if suffix not in allowed:
                raise HTTPException(status_code=400, detail=f"Formato nao suportado: {suffix}")
            path = task_dir / _safe_name(image.filename)
            digest = hashlib.sha256()
            with path.open("wb") as output:
                while chunk := await image.read(1024 * 1024):
                    output.write(chunk)
                    digest.update(chunk)
            paths.append(path)
            digests[path.name] = digest.hexdigest()
        fields = {"name": name}
        if options:
            try:
                json.loads(options)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail=f"options invalido: {exc.msg}")
            fields["options"] = options
        handles = []
        try:
            handles = [("images", (p.name, p.open("rb"), "application/octet-stream")) for p in paths]
            response = requests.post(f"{NODEODM_URL}/task/new", data=fields, files=handles, timeout=120)
            response.raise_for_status()
            payload = response.json()
        finally:
            for _, (_, handle, _) in handles:
                handle.close()
        (task_dir / "manifest.json").write_text(json.dumps({"name": name, "images": [p.name for p in paths], "nodeodm": payload}, ensure_ascii=False), encoding="utf-8")
        task_id = payload.get("uuid")
        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT id FROM voos WHERE id = %s AND projeto_id = %s", (voo_id, projeto_id))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Voo nao encontrado neste projeto")
            cur.execute("INSERT INTO processamentos_odm (projeto_id, voo_id, odm_task_id, endpoint, parametros, status, criado_por) VALUES (%s, %s, %s, %s, %s, 'processando', %s) RETURNING id", (projeto_id, voo_id, task_id, NODEODM_URL, options or "{}", user["id"]))
            processing_id = cur.fetchone()["id"]
            for path in paths:
                cur.execute("INSERT INTO voo_fotos (voo_id, caminho, nome_original, hash_sha256, tamanho_bytes, mime_type, validacao) VALUES (%s, %s, %s, %s, %s, %s, 'valida')", (voo_id, str(path.relative_to(DATA_DIR)), path.name, digests[path.name], path.stat().st_size, "image/" + path.suffix.lower().lstrip(".")))
            conn.commit()
        return {"task": payload, "processamento_id": processing_id, "local_upload": str(task_dir.relative_to(DATA_DIR)), "images_count": len(paths)}
    except HTTPException:
        raise
    except requests.RequestException as exc:
        logger.exception("NodeODM submission failed")
        raise HTTPException(status_code=502, detail=f"NodeODM indisponivel: {exc}")
    except Exception as exc:
        logger.exception("ODM task creation failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/odm/tasks/{task_id}")
async def get_odm_task(task_id: str):
    """Return the live NodeODM status for a task."""
    try:
        response = requests.get(f"{NODEODM_URL}/task/{task_id}/info", timeout=30)
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Tarefa ODM nao encontrada")
        response.raise_for_status()
        return response.json()
    except HTTPException:
        raise
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"NodeODM indisponivel: {exc}")


@router.get("/odm/processamentos")
async def list_processamentos(projeto_id: int = Query(...), user: dict = Depends(current_user)):
    """List local ODM jobs and refresh their state from NodeODM."""
    require_project_role(projeto_id, user, {"proprietario", "editor", "visualizador"})
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM processamentos_odm WHERE projeto_id = %s ORDER BY criado_em DESC", (projeto_id,))
        jobs = [dict(row) for row in cur.fetchall()]
        for job in jobs:
            try:
                info_response = requests.get(f"{job['endpoint']}/task/{job['odm_task_id']}/info", timeout=10)
                if info_response.ok:
                    info = info_response.json(); code = (info.get("status") or {}).get("code")
                    status = {10: "pendente", 20: "processando", 30: "erro", 40: "concluido", 50: "cancelado"}.get(code, job["status"])
                    etapa = (info.get("status") or {}).get("name")
                    cur.execute("UPDATE processamentos_odm SET status = %s, progresso = %s, etapa = %s, atualizado_em = now() WHERE id = %s", (status, info.get("progress", 0), etapa, job["id"]))
                    job.update(status=status, progresso=info.get("progress", 0), etapa=etapa)
            except requests.RequestException:
                pass
        conn.commit()
    return {"total": len(jobs), "processamentos": jobs}


@router.post("/odm/processamentos/{processing_id}/importar")
async def import_odm_products(processing_id: int, user: dict = Depends(current_user)):
    """Download and catalog products from a completed NodeODM task."""
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM processamentos_odm WHERE id = %s", (processing_id,)); job = cur.fetchone()
        if not job: raise HTTPException(status_code=404, detail="Processamento nao encontrado")
        require_project_role(job["projeto_id"], user, {"proprietario", "editor"})
        cur.execute("SELECT id FROM produtos_processamento WHERE processamento_id = %s", (processing_id,))
        if cur.fetchone(): return {"processing_id": processing_id, "message": "Produtos ja importados"}
    try:
        response = requests.get(f"{job['endpoint']}/task/{job['odm_task_id']}/download/all.zip", timeout=300)
        response.raise_for_status()
        work = ODM_UPLOADS_DIR / f"import_{processing_id}_{uuid.uuid4().hex[:8]}"; work.mkdir(parents=True)
        archive = work / "results.zip"; archive.write_bytes(response.content)
        with zipfile.ZipFile(archive) as zf:
            for member in zf.infolist():
                target = (work / member.filename).resolve()
                if not str(target).startswith(str(work.resolve()) + os.sep): raise HTTPException(status_code=400, detail="Arquivo invalido no pacote ODM")
            zf.extractall(work)
        extracted = work / "odm_orthophoto" / "odm_orthophoto.tif"
        if not extracted.exists(): raise HTTPException(status_code=422, detail="Ortofoto nao encontrada no resultado ODM")
        products = []
        for candidate, kind in [(extracted, "ortomosaico"), (work / "odm_dem" / "dsm.tif", "dsm"), (work / "odm_dem" / "dtm.tif", "dtm")]:
            if candidate.exists(): products.append((candidate, kind))
        stored = []
        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            for source, kind in products:
                destination = Path(DATA_DIR) / "ortomapas" / f"odm_{processing_id}_{kind}.tif"; shutil.copy2(source, destination)
                with rasterio.open(destination) as ds:
                    bounds = ds.bounds; crs = str(ds.crs) if ds.crs else None
                    if ds.crs and ds.crs.to_epsg() != 4326:
                        tx = Transformer.from_crs(ds.crs, "EPSG:4326", always_xy=True); west, south = tx.transform(bounds.left, bounds.bottom); east, north = tx.transform(bounds.right, bounds.top)
                    else: west, south, east, north = bounds.left, bounds.bottom, bounds.right, bounds.top
                    cur.execute("INSERT INTO ortomapas (voo_id, projeto_id, nome, tipo, formato, resolucao_cm, largura_px, altura_px, tamanho_arquivo_mb, sistema_coordenadas, bbox_norte, bbox_sul, bbox_leste, bbox_oeste, centro_lat, centro_lon, caminho_arquivo, webodm_task_id, status, data_processamento) VALUES (%s,%s,%s,%s,'GeoTIFF',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'disponivel',now()) RETURNING id", (job["voo_id"], job["projeto_id"], f"ODM {kind} {job['odm_task_id'][:8]}", kind, abs(ds.transform.a) * 100, ds.width, ds.height, destination.stat().st_size / 1048576, crs, north, south, east, west, (north + south) / 2, (east + west) / 2, str(destination.relative_to(DATA_DIR)), job["odm_task_id"]))
                    orto_id = cur.fetchone()["id"]
                    cur.execute("INSERT INTO produtos_processamento (processamento_id, ortomapa_id, tipo, caminho, formato, tamanho_arquivo_mb, crs, resolucao, largura_px, altura_px, bandas) VALUES (%s,%s,%s,%s,'GeoTIFF',%s,%s,%s,%s,%s,%s)", (processing_id, orto_id, kind, str(destination.relative_to(DATA_DIR)), destination.stat().st_size / 1048576, crs, abs(ds.transform.a), ds.width, ds.height, ds.count))
                    stored.append({"id": orto_id, "tipo": kind, "caminho": str(destination.relative_to(DATA_DIR))})
            for source, kind in [(work / "odm_report" / "report.pdf", "relatorio"), (work / "odm_georeferencing" / "odm_georeferenced_model.laz", "nuvem_pontos")]:
                if source.exists():
                    destination = Path(DATA_DIR) / "exports" / f"odm_{processing_id}_{kind}{source.suffix}"; shutil.copy2(source, destination)
                    cur.execute("INSERT INTO produtos_processamento (processamento_id, tipo, caminho, formato, tamanho_arquivo_mb) VALUES (%s,%s,%s,%s,%s)", (processing_id, kind, str(destination.relative_to(DATA_DIR)), source.suffix.lstrip('.').upper(), destination.stat().st_size / 1048576))
            cur.execute("UPDATE processamentos_odm SET status = 'concluido', atualizado_em = now() WHERE id = %s", (processing_id,)); conn.commit()
        return {"processing_id": processing_id, "produtos": stored, "message": "Produtos importados"}
    except HTTPException: raise
    except (requests.RequestException, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao obter resultado ODM: {exc}")
    except Exception as exc:
        logger.exception("ODM product import failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/odm/produtos/{product_id}/points")
async def sample_point_cloud(product_id: int, max_points: int = Query(100000, ge=1000, le=300000), user: dict = Depends(current_user)):
    """Return a bounded LAZ sample for WebGL visualization."""
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True); cur.execute("SELECT p.*, COALESCE(o.projeto_id, j.projeto_id) AS projeto_id FROM produtos_processamento p LEFT JOIN ortomapas o ON o.id = p.ortomapa_id JOIN processamentos_odm j ON j.id = p.processamento_id WHERE p.id = %s AND p.tipo = 'nuvem_pontos'", (product_id,)); product = cur.fetchone()
    if not product: raise HTTPException(status_code=404, detail="Nuvem de pontos nao encontrada")
    require_project_role(product["projeto_id"], user, {"proprietario", "editor", "visualizador"})
    path = Path(DATA_DIR) / product["caminho"]
    if not path.exists(): raise HTTPException(status_code=404, detail="Arquivo LAZ nao encontrado")
    try:
        cloud = laspy.read(path); total = len(cloud.x); step = max(1, total // max_points); idx = slice(None, None, step)
        xs = np.asarray(cloud.x)[idx].astype(float).tolist()
        ys = np.asarray(cloud.y)[idx].astype(float).tolist()
        zs = np.asarray(cloud.z)[idx].astype(float).tolist()
        names = set(cloud.point_format.dimension_names)
        intensity = np.asarray(cloud.intensity)[idx].astype(int).tolist() if "intensity" in names else []
        return {"total": total, "sampled": len(xs), "bounds": {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}, "points": {"x": xs, "y": ys, "z": zs, "intensity": intensity}}
    except Exception as exc:
        logger.exception("Point cloud sampling failed"); raise HTTPException(status_code=500, detail=f"Falha ao ler LAZ: {exc}")


@router.get("/odm/produtos/{product_id}/surface")
async def sample_surface(product_id: int, max_size: int = Query(128, ge=32, le=256), user: dict = Depends(current_user)):
    """Return a bounded DSM elevation grid suitable for WebGL terrain rendering."""
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT p.*, COALESCE(o.projeto_id, j.projeto_id) AS projeto_id FROM produtos_processamento p LEFT JOIN ortomapas o ON o.id = p.ortomapa_id JOIN processamentos_odm j ON j.id = p.processamento_id WHERE p.id = %s AND p.tipo IN ('dsm','dtm')", (product_id,)); product = cur.fetchone()
    if not product: raise HTTPException(status_code=404, detail="Superficie nao encontrada")
    require_project_role(product["projeto_id"], user, {"proprietario", "editor", "visualizador"})
    path = Path(DATA_DIR) / product["caminho"]
    if not path.exists(): raise HTTPException(status_code=404, detail="Arquivo raster nao encontrado")
    try:
        with rasterio.open(path) as ds:
            height = min(max_size, ds.height); width = min(max_size, ds.width)
            grid = ds.read(1, out_shape=(height, width), resampling=rasterio.enums.Resampling.bilinear, masked=True)
            values = np.asarray(grid.filled(np.nan), dtype=float); valid = values[np.isfinite(values)]
            if valid.size: values[~np.isfinite(values)] = float(np.min(valid))
            else: values.fill(0)
            bounds = ds.bounds
            return {"width": width, "height": height, "bounds": [bounds.left, bounds.bottom, bounds.right, bounds.top], "crs": str(ds.crs) if ds.crs else None, "min": float(np.min(values)), "max": float(np.max(values)), "elevations": values.tolist()}
    except Exception as exc:
        logger.exception("DSM sampling failed"); raise HTTPException(status_code=500, detail=f"Falha ao ler DSM: {exc}")


@router.get("/odm/produtos")
async def list_odm_products(projeto_id: int = Query(...), user: dict = Depends(current_user)):
    """List imported ODM products, including non-raster assets such as LAZ."""
    require_project_role(projeto_id, user, {"proprietario", "editor", "visualizador"})
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT p.*, j.projeto_id, j.odm_task_id
                       FROM produtos_processamento p
                       JOIN processamentos_odm j ON j.id = p.processamento_id
                       WHERE j.projeto_id = %s ORDER BY p.criado_em DESC, p.id DESC""", (projeto_id,))
        return {"produtos": [dict(row) for row in cur.fetchall()]}


@router.get("/odm/processamentos/{processing_id}/elevacao-diferenca")
async def elevation_difference(processing_id: int, max_size: int = Query(128, ge=32, le=256), user: dict = Depends(current_user)):
    """Compare DSM and DTM from one processing and return a bounded difference grid."""
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM processamentos_odm WHERE id = %s", (processing_id,)); job = cur.fetchone()
        cur.execute("SELECT * FROM produtos_processamento WHERE processamento_id = %s AND tipo IN ('dsm','dtm')", (processing_id,)); products = {r['tipo']: r for r in cur.fetchall()}
    if not job or not {'dsm', 'dtm'}.issubset(products): raise HTTPException(status_code=404, detail="DSM e DTM nao encontrados")
    require_project_role(job['projeto_id'], user, {'proprietario', 'editor', 'visualizador'})
    try:
        with rasterio.open(Path(DATA_DIR) / products['dsm']['caminho']) as dsm, rasterio.open(Path(DATA_DIR) / products['dtm']['caminho']) as dtm:
            height = min(max_size, dsm.height, dtm.height); width = min(max_size, dsm.width, dtm.width)
            a = dsm.read(1, out_shape=(height, width), resampling=rasterio.enums.Resampling.bilinear, masked=True).filled(np.nan)
            b = dtm.read(1, out_shape=(height, width), resampling=rasterio.enums.Resampling.bilinear, masked=True).filled(np.nan)
            diff = np.asarray(a - b, dtype=float); valid = diff[np.isfinite(diff)]
            if not valid.size: raise HTTPException(status_code=422, detail="Produtos sem dados validos")
            diff[~np.isfinite(diff)] = 0
            return {'width': width, 'height': height, 'min': float(valid.min()), 'max': float(valid.max()), 'mean': float(valid.mean()), 'bounds': [dsm.bounds.left, dsm.bounds.bottom, dsm.bounds.right, dsm.bounds.top], 'differences': diff.tolist()}
    except HTTPException: raise
    except Exception as exc:
        logger.exception("Elevation comparison failed"); raise HTTPException(status_code=500, detail=f"Falha ao comparar DSM e DTM: {exc}")


@router.get("/odm/tasks/{task_id}/download/{asset}")
async def download_odm_asset(task_id: str, asset: str):
    """Expose a validated download URL for a NodeODM asset."""
    if asset not in {"all.zip", "orthophoto.tif", "dsm.tif", "dtm.tif"}:
        raise HTTPException(status_code=400, detail="Asset ODM nao permitido")
    return {"url": f"{NODEODM_URL}/task/{task_id}/download/{asset}"}
