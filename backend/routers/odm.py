"""NodeODM integration endpoints for importing and monitoring photo tasks."""

import json
import hashlib
import logging
import os
import re
import uuid
import zipfile
import shutil
import time
from fastapi.responses import FileResponse
import rasterio
import laspy
import numpy as np
from pyproj import Transformer
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Query
from PIL import Image
from psycopg2.extras import Json

from backend.config import DATA_DIR, NODEODM_URL
from backend.database.connection import get_connection
from backend.routers.auth import current_user, require_project_role

logger = logging.getLogger(__name__)
router = APIRouter()
ODM_UPLOADS_DIR = Path(DATA_DIR) / "odm_uploads"
ODM_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
_POINT_CACHE = {}
_POINT_CACHE_TTL = 300
_POINT_CACHE_MAX = 8
MAX_ODM_IMAGES = 500
MAX_ODM_IMAGE_BYTES = 100 * 1024 * 1024
MAX_ODM_UPLOAD_BYTES = 2 * 1024 * 1024 * 1024


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
    if len(images) < 3:
        raise HTTPException(status_code=422, detail="A fotogrametria requer ao menos 3 imagens")
    if len(images) > MAX_ODM_IMAGES:
        raise HTTPException(status_code=413, detail=f"Limite de {MAX_ODM_IMAGES} imagens por processamento")
    require_project_role(projeto_id, user, {"proprietario", "editor"})
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM voos WHERE id = %s AND projeto_id = %s", (voo_id, projeto_id))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Voo nao encontrado neste projeto")
    allowed = {".jpg", ".jpeg", ".tif", ".tiff"}
    task_dir = ODM_UPLOADS_DIR / str(uuid.uuid4())
    task_dir.mkdir(parents=True)
    paths = []
    digests = {}
    image_metadata = {}
    total_bytes = 0
    persisted = False
    try:
        for image in images:
            suffix = Path(image.filename or "").suffix.lower()
            if suffix not in allowed:
                raise HTTPException(status_code=400, detail=f"Formato nao suportado: {suffix}")
            safe_name = _safe_name(image.filename)
            if safe_name in image_metadata:
                raise HTTPException(status_code=422, detail=f"Nome de arquivo duplicado: {safe_name}")
            path = task_dir / safe_name
            digest = hashlib.sha256()
            file_bytes = 0
            with path.open("wb") as output:
                while chunk := await image.read(1024 * 1024):
                    file_bytes += len(chunk)
                    total_bytes += len(chunk)
                    if file_bytes > MAX_ODM_IMAGE_BYTES or total_bytes > MAX_ODM_UPLOAD_BYTES:
                        raise HTTPException(status_code=413, detail="Upload excede o limite de 100 MB por foto ou 2 GB por tarefa")
                    output.write(chunk)
                    digest.update(chunk)
            if file_bytes == 0:
                raise HTTPException(status_code=422, detail=f"Imagem vazia: {safe_name}")
            if digest.hexdigest() in digests.values():
                raise HTTPException(status_code=422, detail=f"Imagem duplicada: {safe_name}")
            try:
                with Image.open(path) as picture:
                    picture.verify()
                with Image.open(path) as picture:
                    exif = picture.getexif()
                    gps = exif.get_ifd(34853) if 34853 in exif else {}
                    image_metadata[safe_name] = {
                        "width": picture.width,
                        "height": picture.height,
                        "format": picture.format,
                        "camera_model": exif.get(272),
                        "captured_at": exif.get(36867),
                        "has_gps": bool(gps),
                    }
            except Exception as exc:
                raise HTTPException(status_code=422, detail=f"Imagem invalida ou ilegivel: {safe_name}") from exc
            paths.append(path)
            digests[path.name] = digest.hexdigest()
        geotagged = sum(1 for metadata in image_metadata.values() if metadata["has_gps"])
        if geotagged < 3:
            raise HTTPException(status_code=422, detail="Ao menos 3 imagens precisam conter coordenadas GPS EXIF para georreferenciar o processamento")
        fields = {"name": name}
        if options:
            try:
                parsed_options = json.loads(options)
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=400, detail=f"options invalido: {exc.msg}")
            if not isinstance(parsed_options, (list, dict)):
                raise HTTPException(status_code=400, detail="options deve ser uma lista ou objeto JSON")
            fields["options"] = options
        handles = []
        try:
            handles = [("images", (p.name, p.open("rb"), "application/octet-stream")) for p in paths]
            response = requests.post(f"{NODEODM_URL}/task/new", data=fields, files=handles, timeout=120)
            response.raise_for_status()
            payload = response.json()
            if not payload.get("uuid"):
                raise HTTPException(status_code=502, detail="NodeODM respondeu sem o identificador da tarefa")
        finally:
            for _, (_, handle, _) in handles:
                handle.close()
        (task_dir / "manifest.json").write_text(json.dumps({"name": name, "images": [p.name for p in paths], "nodeodm": payload}, ensure_ascii=False), encoding="utf-8")
        task_id = payload.get("uuid")
        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("INSERT INTO processamentos_odm (projeto_id, voo_id, odm_task_id, endpoint, parametros, status, criado_por) VALUES (%s, %s, %s, %s, %s, 'pendente', %s) RETURNING id", (projeto_id, voo_id, task_id, NODEODM_URL, Json(json.loads(options) if options else {}), user["id"]))
            processing_id = cur.fetchone()["id"]
            for path in paths:
                cur.execute("INSERT INTO voo_fotos (voo_id, caminho, nome_original, hash_sha256, tamanho_bytes, mime_type, exif, validacao) VALUES (%s, %s, %s, %s, %s, %s, %s, 'valida')", (voo_id, str(path.relative_to(DATA_DIR)), path.name, digests[path.name], path.stat().st_size, "image/" + path.suffix.lower().lstrip("."), Json(image_metadata[path.name])))
            cur.execute("UPDATE voos SET num_fotos = %s, fotos_path = %s WHERE id = %s", (len(paths), str(task_dir.relative_to(DATA_DIR)), voo_id))
            conn.commit()
            persisted = True
        return {"task": payload, "processamento_id": processing_id, "local_upload": str(task_dir.relative_to(DATA_DIR)), "images_count": len(paths), "geotagged_count": geotagged}
    except HTTPException:
        if not persisted:
            shutil.rmtree(task_dir, ignore_errors=True)
        raise
    except requests.RequestException as exc:
        logger.exception("NodeODM submission failed")
        shutil.rmtree(task_dir, ignore_errors=True)
        raise HTTPException(status_code=502, detail=f"NodeODM indisponivel: {exc}")
    except Exception as exc:
        logger.exception("ODM task creation failed")
        if not persisted:
            shutil.rmtree(task_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/odm/tasks/{task_id}")
async def get_odm_task(task_id: str, user: dict = Depends(current_user)):
    """Return the live NodeODM status for a task."""
    try:
        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT projeto_id, endpoint FROM processamentos_odm WHERE odm_task_id = %s", (task_id,))
            job = cur.fetchone()
        if not job:
            raise HTTPException(status_code=404, detail="Tarefa ODM nao encontrada")
        require_project_role(job["projeto_id"], user, {"proprietario", "editor", "visualizador"})
        response = requests.get(f"{job['endpoint']}/task/{task_id}/info", timeout=30)
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
                    info = info_response.json(); node_status = info.get("status") or {}; code = node_status.get("code")
                    status = {10: "pendente", 20: "processando", 30: "erro", 40: "concluido", 50: "cancelado"}.get(code, job["status"])
                    etapa = node_status.get("name")
                    error = node_status.get("error") or node_status.get("message") if status == "erro" else None
                    progress = max(0, min(100, float(info.get("progress") or 0)))
                    cur.execute("""UPDATE processamentos_odm SET status = %s, progresso = %s, etapa = %s, erro = %s,
                        inicio_em = CASE WHEN %s = 'processando' THEN COALESCE(inicio_em, now()) ELSE inicio_em END,
                        fim_em = CASE WHEN %s IN ('concluido','erro','cancelado') THEN COALESCE(fim_em, now()) ELSE fim_em END,
                        atualizado_em = now() WHERE id = %s""", (status, progress, etapa, error, status, status, job["id"]))
                    job.update(status=status, progresso=progress, etapa=etapa, erro=error)
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
        cur.execute("SELECT id, tipo, caminho FROM produtos_processamento WHERE processamento_id = %s ORDER BY id", (processing_id,))
        existing_products = [dict(row) for row in cur.fetchall()]
        if existing_products:
            return {"processing_id": processing_id, "message": "Produtos ja importados", "produtos": existing_products}
    work = None
    created_files = []
    committed = False
    try:
        info_response = requests.get(f"{job['endpoint']}/task/{job['odm_task_id']}/info", timeout=30)
        info_response.raise_for_status()
        if (info_response.json().get("status") or {}).get("code") != 40:
            raise HTTPException(status_code=409, detail="A tarefa NodeODM ainda nao foi concluida")
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
                destination = Path(DATA_DIR) / "ortomapas" / f"odm_{processing_id}_{kind}.tif"; shutil.copy2(source, destination); created_files.append(destination)
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
                    destination = Path(DATA_DIR) / "exports" / f"odm_{processing_id}_{kind}{source.suffix}"; shutil.copy2(source, destination); created_files.append(destination)
                    cur.execute("INSERT INTO produtos_processamento (processamento_id, tipo, caminho, formato, tamanho_arquivo_mb) VALUES (%s,%s,%s,%s,%s)", (processing_id, kind, str(destination.relative_to(DATA_DIR)), source.suffix.lstrip('.').upper(), destination.stat().st_size / 1048576))
            cur.execute("UPDATE processamentos_odm SET status = 'concluido', progresso = 100, etapa = 'Produtos importados', erro = NULL, fim_em = COALESCE(fim_em, now()), atualizado_em = now() WHERE id = %s", (processing_id,)); conn.commit(); committed = True
        return {"processing_id": processing_id, "produtos": stored, "message": "Produtos importados"}
    except HTTPException:
        raise
    except (requests.RequestException, zipfile.BadZipFile) as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao obter resultado ODM: {exc}")
    except Exception as exc:
        logger.exception("ODM product import failed")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if work:
            shutil.rmtree(work, ignore_errors=True)
        if not committed:
            for path in created_files:
                path.unlink(missing_ok=True)


@router.get("/odm/produtos/{product_id}/points")
async def sample_point_cloud(product_id: int, max_points: int = Query(100000, ge=1000, le=300000), xmin: Optional[float] = Query(None), xmax: Optional[float] = Query(None), ymin: Optional[float] = Query(None), ymax: Optional[float] = Query(None), user: dict = Depends(current_user)):
    """Return a bounded LAZ sample for WebGL visualization."""
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True); cur.execute("SELECT p.*, COALESCE(o.projeto_id, j.projeto_id) AS projeto_id FROM produtos_processamento p LEFT JOIN ortomapas o ON o.id = p.ortomapa_id JOIN processamentos_odm j ON j.id = p.processamento_id WHERE p.id = %s AND p.tipo = 'nuvem_pontos'", (product_id,)); product = cur.fetchone()
    if not product: raise HTTPException(status_code=404, detail="Nuvem de pontos nao encontrada")
    require_project_role(product["projeto_id"], user, {"proprietario", "editor", "visualizador"})
    cache_key = (product_id, max_points, xmin, xmax, ymin, ymax); cached = _POINT_CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _POINT_CACHE_TTL: return cached[1]
    path = Path(DATA_DIR) / product["caminho"]
    if not path.exists(): raise HTTPException(status_code=404, detail="Arquivo LAZ nao encontrado")
    try:
        cloud = laspy.read(path); total = len(cloud.x); mask = np.ones(total, dtype=bool)
        crs = cloud.header.parse_crs()
        if not crs or not crs.is_projected:
            raise HTTPException(status_code=422, detail="Nuvem sem CRS projetado: medidas metricas indisponiveis")
        if any(v is not None for v in (xmin, xmax, ymin, ymax)):
            if any(v is None for v in (xmin, xmax, ymin, ymax)):
                raise HTTPException(status_code=400, detail="Recorte deve informar todos os limites WGS84")
            from rasterio.warp import transform_bounds
            xmin, ymin, xmax, ymax = transform_bounds("EPSG:4326", crs, xmin, ymin, xmax, ymax)
        if xmin is not None: mask &= np.asarray(cloud.x) >= xmin
        if xmax is not None: mask &= np.asarray(cloud.x) <= xmax
        if ymin is not None: mask &= np.asarray(cloud.y) >= ymin
        if ymax is not None: mask &= np.asarray(cloud.y) <= ymax
        candidates = np.flatnonzero(mask); step = max(1, int(np.ceil(len(candidates) / max_points))); idx = candidates[::step]
        xs = np.asarray(cloud.x)[idx].astype(float).tolist()
        ys = np.asarray(cloud.y)[idx].astype(float).tolist()
        zs = np.asarray(cloud.z)[idx].astype(float).tolist()
        names = set(cloud.point_format.dimension_names)
        intensity = np.asarray(cloud.intensity)[idx].astype(int).tolist() if "intensity" in names else []
        if not xs: raise HTTPException(status_code=422, detail="Recorte sem pontos")
        factor = crs.axis_info[0].unit_conversion_factor
        if abs(factor - 1) > 1e-9:
            xs = [v * factor for v in xs]; ys = [v * factor for v in ys]; zs = [v * factor for v in zs]
        result = {"units": "m", "source_crs": crs.to_string(), "total": total, "candidates": len(candidates), "sampled": len(xs), "bounds": {"min": [min(xs), min(ys), min(zs)], "max": [max(xs), max(ys), max(zs)]}, "points": {"x": xs, "y": ys, "z": zs, "intensity": intensity}}
        _POINT_CACHE[cache_key] = (time.time(), result)
        while len(_POINT_CACHE) > _POINT_CACHE_MAX:
            oldest = min(_POINT_CACHE, key=lambda key: _POINT_CACHE[key][0]); _POINT_CACHE.pop(oldest, None)
        return result
    except HTTPException:
        raise
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
        from backend.utils.surface_grid import metric_surface
        return metric_surface(path, max_size)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
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


@router.get("/odm/produtos/{product_id}/download")
async def download_product(product_id: int, user: dict = Depends(current_user)):
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True); cur.execute("SELECT p.*, j.projeto_id FROM produtos_processamento p JOIN processamentos_odm j ON j.id = p.processamento_id WHERE p.id = %s", (product_id,)); product = cur.fetchone()
    if not product: raise HTTPException(status_code=404, detail="Produto nao encontrado")
    require_project_role(product['projeto_id'], user, {'proprietario', 'editor', 'visualizador'})
    path = Path(DATA_DIR) / product['caminho']
    if not path.exists(): raise HTTPException(status_code=404, detail="Arquivo nao encontrado")
    return FileResponse(path, filename=path.name, media_type='application/pdf' if product['tipo'] == 'relatorio' else 'application/octet-stream')


@router.get("/odm/processamentos/{processing_id}/elevacao-diferenca")
async def elevation_difference(processing_id: int, max_size: int = Query(128, ge=32, le=256), user: dict = Depends(current_user)):
    """Compare DSM and DTM from one processing and return a bounded difference grid."""
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM processamentos_odm WHERE id = %s", (processing_id,)); job = cur.fetchone()
        cur.execute("SELECT * FROM produtos_processamento WHERE processamento_id = %s AND tipo IN ('dsm','dtm')", (processing_id,)); products = {r['tipo']: r for r in cur.fetchall()}
    if not job or not {'dsm', 'dtm'}.issubset(products): raise HTTPException(status_code=404, detail="DSM e DTM nao encontrados")
    require_project_role(job['projeto_id'], user, {'proprietario', 'editor', 'visualizador'})
    try:
        from backend.utils.elevation_analysis import aligned_difference
        return aligned_difference(Path(DATA_DIR)/products['dsm']['caminho'],Path(DATA_DIR)/products['dtm']['caminho'],max_size)
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc))
    except HTTPException: raise
    except Exception as exc:
        logger.exception("Elevation comparison failed"); raise HTTPException(status_code=500, detail=f"Falha ao comparar DSM e DTM: {exc}")


@router.get("/odm/processamentos/{processing_id}/qualidade")
async def processing_quality(processing_id: int, user: dict = Depends(current_user)):
    """Deterministic quality summary used by the future AI advisor."""
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True); cur.execute("SELECT * FROM processamentos_odm WHERE id = %s", (processing_id,)); job = cur.fetchone(); cur.execute("SELECT tipo, caminho, tamanho_arquivo_mb FROM produtos_processamento WHERE processamento_id = %s", (processing_id,)); products = cur.fetchall()
    if not job: raise HTTPException(status_code=404, detail="Processamento nao encontrado")
    require_project_role(job['projeto_id'], user, {'proprietario', 'editor', 'visualizador'})
    kinds = {p['tipo'] for p in products}; checks = [{'item': 'ortomosaico', 'ok': 'ortomosaico' in kinds}, {'item': 'modelo de elevacao', 'ok': bool({'dsm', 'dtm'} & kinds)}, {'item': 'nuvem de pontos', 'ok': 'nuvem_pontos' in kinds}]; metrics = {}
    cloud = next((p for p in products if p['tipo'] == 'nuvem_pontos'), None)
    if cloud:
        try:
            with laspy.open(Path(DATA_DIR) / cloud['caminho']) as reader: metrics['pontos_laz'] = reader.header.point_count
        except Exception: metrics['pontos_laz'] = None
    for kind in ('dsm', 'dtm', 'ortomosaico'):
        item = next((p for p in products if p['tipo'] == kind), None)
        if item:
            try:
                with rasterio.open(Path(DATA_DIR) / item['caminho']) as ds: metrics[f'{kind}_pixels'] = ds.width * ds.height; metrics[f'{kind}_resolucao'] = abs(ds.transform.a)
            except Exception: pass
    # Some LAZ headers do not expose a usable point count. Treat that as an
    # unavailable metric, rather than raising while rendering the quality card.
    laz_points = metrics.get('pontos_laz')
    if laz_points is None or laz_points < 100000: checks[2]['ok'] = False
    score = round(sum(c['ok'] for c in checks) / len(checks) * 100); recommendations = []
    if 'ortomosaico' not in kinds: recommendations.append('Reprocessar solicitando ortomosaico.')
    if not ({'dsm', 'dtm'} & kinds): recommendations.append('Gerar DSM ou DTM para análise altimétrica.')
    if laz_points is None:
        recommendations.append('Não foi possível ler a contagem de pontos LAZ; revisar o cabeçalho da nuvem.')
    elif laz_points < 100000:
        recommendations.append('Revisar sobreposição e qualidade das imagens: nuvem de pontos abaixo do esperado.')
    if not recommendations: recommendations.append('Produtos principais presentes; revisar o relatório ODM para validação final.')
    return {'processamento_id': processing_id, 'score': score, 'nivel': 'bom' if score >= 80 else 'atencao', 'verificacoes': checks, 'metricas': metrics, 'recomendacoes': recommendations, 'produtos': products}


@router.get("/odm/tasks/{task_id}/download/{asset}")
async def download_odm_asset(task_id: str, asset: str, user: dict = Depends(current_user)):
    """Expose a validated download URL for a NodeODM asset."""
    if asset not in {"all.zip", "orthophoto.tif", "dsm.tif", "dtm.tif"}:
        raise HTTPException(status_code=400, detail="Asset ODM nao permitido")
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT projeto_id, endpoint FROM processamentos_odm WHERE odm_task_id = %s", (task_id,))
        job = cur.fetchone()
    if not job:
        raise HTTPException(status_code=404, detail="Tarefa ODM nao encontrada")
    require_project_role(job["projeto_id"], user, {"proprietario", "editor", "visualizador"})
    return {"url": f"{job['endpoint']}/task/{task_id}/download/{asset}"}
