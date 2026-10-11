"""
Router for Ortomapas CRUD, file upload, tile serving, and spatial queries.
"""

import io
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from backend.routers.auth import current_user, require_project_role
from backend.utils.resource_access import media_user, media_ticket, data_path, file_projects, READ_ROLES
from fastapi.responses import StreamingResponse

from backend.config import DATA_DIR, ORTOMAPAS_DIR, THUMBNAILS_DIR
from backend.database.connection import get_connection
from backend.utils.file_manager import save_upload, get_file_size_mb
from backend.utils.geo_utils import get_raster_info, get_raster_bounds
from backend.utils.thumbnail import generate_thumbnail
from backend.utils.raster_tiles import render_xyz_tile, tile_bounds

logger = logging.getLogger(__name__)
router = APIRouter()


def validate_flight(project_id, flight_id, user):
    require_project_role(project_id, user, {"proprietario", "editor"})
    if not flight_id:
        raise HTTPException(status_code=400, detail="Campo 'voo_id' e obrigatorio")
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id FROM voos WHERE id=%s AND projeto_id=%s", (flight_id, project_id))
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail="Voo nao pertence ao projeto")


@router.get("/ortomapas/spatial")
async def spatial_query(
    norte: float = Query(..., description="North latitude"),
    sul: float = Query(..., description="South latitude"),
    leste: float = Query(..., description="East longitude"),
    oeste: float = Query(..., description="West longitude"),
    user: dict = Depends(current_user),
):
    """Query ortomapas that intersect the given bounding box."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT * FROM ortomapas
                WHERE bbox_norte >= %s AND bbox_sul <= %s
                  AND bbox_leste >= %s AND bbox_oeste <= %s
                  AND (%s='admin' OR projeto_id IN (SELECT projeto_id FROM projeto_usuarios WHERE usuario_id=%s))
                ORDER BY criado_em DESC
                """,
                (sul, norte, oeste, leste, user["perfil"], user["id"]),
            )
            rows = cursor.fetchall()
            return {"total": len(rows), "ortomapas": rows}
    except Exception as e:
        logger.error(f"Error in spatial query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ortomapas")
async def list_ortomapas(
    projeto_id: Optional[int] = Query(None, description="Filter by projeto_id"),
    tipo: Optional[str] = Query(None, description="Filter by tipo"),
    status: Optional[str] = Query(None, description="Filter by status"),
    user: dict = Depends(current_user),
):
    """List all ortomapas with optional filters."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            if projeto_id is not None:
                require_project_role(projeto_id, user, READ_ROLES)
            query = "SELECT * FROM ortomapas WHERE (%s='admin' OR projeto_id IN (SELECT projeto_id FROM projeto_usuarios WHERE usuario_id=%s))"
            params = [user["perfil"], user["id"]]

            if projeto_id is not None:
                query += " AND projeto_id = %s"
                params.append(projeto_id)
            if tipo:
                query += " AND tipo = %s"
                params.append(tipo)
            if status:
                query += " AND status = %s"
                params.append(status)

            query += " ORDER BY criado_em DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return {"total": len(rows), "ortomapas": rows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing ortomapas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ortomapas/{ortomapa_id}")
async def get_ortomapa(ortomapa_id: int, user: dict = Depends(current_user)):
    """Get a single ortomapa by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM ortomapas WHERE id = %s", (ortomapa_id,))
            ortomapa = cursor.fetchone()
            if not ortomapa:
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")
            require_project_role(ortomapa["projeto_id"], user, READ_ROLES)
            return ortomapa
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ortomapa {ortomapa_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ortomapas", status_code=201)
async def create_ortomapa(data: dict, user: dict = Depends(current_user)):
    """Create ortomapa metadata record."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            projeto_id = data.get("projeto_id")
            if not projeto_id:
                raise HTTPException(
                    status_code=400, detail="Campo 'projeto_id' e obrigatorio"
                )
            validate_flight(projeto_id, data.get("voo_id"), user)
            if data.get("caminho_arquivo"):
                file_projects(data["caminho_arquivo"], user)

            cursor.execute("SELECT id FROM projetos WHERE id = %s", (projeto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

            cursor.execute(
                """
                INSERT INTO ortomapas (
                    projeto_id, voo_id, nome, tipo, formato, caminho_arquivo, resolucao_cm,
                    bbox_norte, bbox_sul, bbox_leste, bbox_oeste,
                    centro_lat, centro_lon,
                    largura_px, altura_px, tamanho_arquivo_mb,
                    sistema_coordenadas, status, observacoes, criado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    projeto_id,
                    data.get("voo_id"),
                    data.get("nome", ""),
                    data.get("tipo", "ortomosaico"),
                    data.get("formato", "GeoTIFF"),
                    data.get("caminho_arquivo", ""),
                    data.get("resolucao_cm"),
                    data.get("bbox_norte"),
                    data.get("bbox_sul"),
                    data.get("bbox_leste"),
                    data.get("bbox_oeste"),
                    data.get("centro_lat"),
                    data.get("centro_lon"),
                    data.get("largura_px"),
                    data.get("altura_px"),
                    data.get("tamanho_arquivo_mb"),
                    data.get("sistema_coordenadas", "EPSG:4326"),
                    data.get("status", "processando"),
                    data.get("observacoes", ""),
                    datetime.utcnow(),
                ),
            )
            new_id = cursor.fetchone()["id"]
            conn.commit()

            cursor.execute("SELECT * FROM ortomapas WHERE id = %s", (new_id,))
            return cursor.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ortomapa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ortomapas/upload", status_code=201)
async def upload_ortomapa(
    file: UploadFile = File(...),
    projeto_id: int = Query(...),
    nome: Optional[str] = Query(None),
    voo_id: Optional[int] = Query(None),
    tipo: str = Query("ortomosaico"),
    user: dict = Depends(current_user),
):
    """
    Upload a GeoTIFF file and auto-extract metadata (bbox, resolution, size)
    using rasterio.
    """
    validate_flight(projeto_id, voo_id, user)
    filepath = None
    thumb_path = None
    try:
        # Save uploaded file
        filepath = await save_upload(file, ORTOMAPAS_DIR)

        # Extract raster metadata
        info = get_raster_info(filepath)
        if not info["crs"]:
            raise HTTPException(status_code=400, detail="GeoTIFF sem sistema de coordenadas")
        north, south, east, west = get_raster_bounds(filepath)
        size_mb = get_file_size_mb(filepath)

        # Calculate resolution in cm (approximate)
        import rasterio
        from pyproj import CRS, Geod
        with rasterio.open(filepath) as ds:
            crs = CRS.from_user_input(ds.crs)
            if crs.is_projected:
                res_cm = abs(ds.res[0]) * crs.axis_info[0].unit_conversion_factor * 100
            else:
                cx, cy = ds.xy(ds.height // 2, ds.width // 2)
                nx, ny = ds.xy(ds.height // 2, ds.width // 2 + 1)
                res_cm = Geod(ellps="WGS84").inv(cx, cy, nx, ny)[2] * 100

        # Generate thumbnail
        thumb_filename = os.path.splitext(os.path.basename(filepath))[0] + "_thumb.png"
        thumb_path = os.path.join(THUMBNAILS_DIR, thumb_filename)
        try:
            generate_thumbnail(filepath, thumb_path)
        except Exception as te:
            logger.warning(f"Thumbnail generation failed: {te}")
            thumb_path = None

        # Save to database
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT id FROM projetos WHERE id = %s", (projeto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

            ortomapa_nome = nome or os.path.basename(filepath)

            cursor.execute(
                """
                INSERT INTO ortomapas (
                    projeto_id, voo_id, nome, tipo, formato, caminho_arquivo, resolucao_cm,
                    bbox_norte, bbox_sul, bbox_leste, bbox_oeste,
                    largura_px, altura_px, tamanho_arquivo_mb,
                    sistema_coordenadas, caminho_thumbnail, status, criado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    projeto_id,
                    voo_id,
                    ortomapa_nome,
                    tipo,
                    "GeoTIFF",
                    filepath,
                    res_cm,
                    north,
                    south,
                    east,
                    west,
                    info["size"]["width"],
                    info["size"]["height"],
                    round(size_mb, 2),
                    info["crs"],
                    thumb_path,
                    "disponivel",
                    datetime.utcnow(),
                ),
            )
            new_id = cursor.fetchone()["id"]
            conn.commit()

            cursor.execute("SELECT * FROM ortomapas WHERE id = %s", (new_id,))
            ortomapa = cursor.fetchone()

        return {
            "ortomapa": ortomapa,
            "raster_info": info,
            "file_size_mb": round(size_mb, 2),
        }
    except HTTPException:
        for path in (filepath, thumb_path):
            if path and os.path.isfile(path):
                os.remove(path)
        raise
    except Exception as e:
        for path in (filepath, thumb_path):
            if path and os.path.isfile(path):
                os.remove(path)
        logger.error(f"Error uploading ortomapa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ortomapas/{ortomapa_id}")
async def update_ortomapa(ortomapa_id: int, data: dict, user: dict = Depends(current_user)):
    """Update an existing ortomapa."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM ortomapas WHERE id = %s", (ortomapa_id,))
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")
            require_project_role(existing["projeto_id"], user, {"proprietario", "editor"})
            if data.get("caminho_arquivo"):
                file_projects(data["caminho_arquivo"], user)

            updatable = [
                "nome", "tipo", "caminho_arquivo", "resolucao_cm",
                "bbox_norte", "bbox_sul", "bbox_leste", "bbox_oeste",
                "largura_px", "altura_px", "tamanho_arquivo_mb",
                "sistema_coordenadas", "status", "observacoes",
            ]

            fields = []
            params = []
            for field in updatable:
                if field in data:
                    fields.append(f"{field} = %s")
                    params.append(data[field])

            if not fields:
                raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

            fields.append("atualizado_em = %s")
            params.append(datetime.utcnow())
            params.append(ortomapa_id)

            cursor.execute(
                f"UPDATE ortomapas SET {', '.join(fields)} WHERE id = %s", params
            )
            conn.commit()

            cursor.execute("SELECT * FROM ortomapas WHERE id = %s", (ortomapa_id,))
            return cursor.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ortomapa {ortomapa_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ortomapas/{ortomapa_id}")
async def delete_ortomapa(ortomapa_id: int, user: dict = Depends(current_user)):
    """Delete an ortomapa and optionally its file."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM ortomapas WHERE id = %s", (ortomapa_id,)
            )
            ortomapa = cursor.fetchone()
            if not ortomapa:
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")
            require_project_role(ortomapa["projeto_id"], user, {"proprietario", "editor"})

            cursor.execute("DELETE FROM ortomapas WHERE id = %s", (ortomapa_id,))
            conn.commit()

        # Files can be shared by imported products; deletion here removes metadata only.

        return {"message": "Ortomapa deletado com sucesso", "id": ortomapa_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ortomapa {ortomapa_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ortomapas/{ortomapa_id}/tile/{z}/{x}/{y}.png")
async def get_tile(ortomapa_id: int, z: int, x: int, y: int, user: dict = Depends(media_user)):
    """Serve a georeferenced 256x256 XYZ tile, preserving source alpha/nodata."""

    try:
        try:
            tile_bounds(z, x, y)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT caminho_arquivo, projeto_id FROM ortomapas WHERE id = %s", (ortomapa_id,)
            )
            ortomapa = cursor.fetchone()
            if not ortomapa:
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")
            require_project_role(ortomapa["projeto_id"], user, READ_ROLES)

            filepath = ortomapa.get("caminho_arquivo")
            if filepath:
                filepath = str(data_path(filepath))
            if filepath and not os.path.isabs(filepath):
                filepath = os.path.join(DATA_DIR, filepath)
            if not filepath or not os.path.exists(filepath):
                raise HTTPException(status_code=404, detail="Arquivo GeoTIFF nao encontrado")

        return StreamingResponse(io.BytesIO(render_xyz_tile(filepath, z, x, y)), media_type="image/png", headers={"Cache-Control": "private, no-store"})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating tile z={z} x={x} y={y} for ortomapa {ortomapa_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ortomapas/{ortomapa_id}/tile-access")
async def tile_access(ortomapa_id: int, user: dict = Depends(current_user)):
    await get_ortomapa(ortomapa_id, user)
    scope = f"/api/ortomapas/{ortomapa_id}/tile/"
    return {"url": scope + "{z}/{x}/{y}.png?ticket=" + media_ticket(user, scope), "expires_in": 300}
