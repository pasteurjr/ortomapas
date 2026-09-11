"""NodeODM integration endpoints for importing and monitoring photo tasks."""

import json
import logging
import os
import re
import uuid
from pathlib import Path
from typing import List, Optional

import requests
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.config import DATA_DIR, NODEODM_URL

logger = logging.getLogger(__name__)
router = APIRouter()
ODM_UPLOADS_DIR = Path(DATA_DIR) / "odm_uploads"
ODM_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", Path(name or "image.jpg").name)


@router.post("/odm/tasks", status_code=202)
async def create_odm_task(
    images: List[UploadFile] = File(...),
    name: str = Form("Ortomapas ODM"),
    options: Optional[str] = Form(None),
):
    """Store flight photos and submit them asynchronously to NodeODM."""
    if not images:
        raise HTTPException(status_code=400, detail="Envie pelo menos uma imagem")
    allowed = {".jpg", ".jpeg", ".tif", ".tiff"}
    task_dir = ODM_UPLOADS_DIR / str(uuid.uuid4())
    task_dir.mkdir(parents=True)
    paths = []
    try:
        for image in images:
            suffix = Path(image.filename or "").suffix.lower()
            if suffix not in allowed:
                raise HTTPException(status_code=400, detail=f"Formato nao suportado: {suffix}")
            path = task_dir / _safe_name(image.filename)
            with path.open("wb") as output:
                while chunk := await image.read(1024 * 1024):
                    output.write(chunk)
            paths.append(path)
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
        return {"task": payload, "local_upload": str(task_dir.relative_to(DATA_DIR)), "images_count": len(paths)}
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


@router.get("/odm/tasks/{task_id}/download/{asset}")
async def download_odm_asset(task_id: str, asset: str):
    """Expose a validated download URL for a NodeODM asset."""
    if asset not in {"all.zip", "orthophoto.tif", "dsm.tif", "dtm.tif"}:
        raise HTTPException(status_code=400, detail="Asset ODM nao permitido")
    return {"url": f"{NODEODM_URL}/task/{task_id}/download/{asset}"}
