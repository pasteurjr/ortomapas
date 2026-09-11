"""NodeODM integration endpoints for importing and monitoring photo tasks."""

import json
import hashlib
import logging
import os
import re
import uuid
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


@router.get("/odm/tasks/{task_id}/download/{asset}")
async def download_odm_asset(task_id: str, asset: str):
    """Expose a validated download URL for a NodeODM asset."""
    if asset not in {"all.zip", "orthophoto.tif", "dsm.tif", "dtm.tif"}:
        raise HTTPException(status_code=400, detail="Asset ODM nao permitido")
    return {"url": f"{NODEODM_URL}/task/{task_id}/download/{asset}"}
