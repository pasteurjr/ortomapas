"""
Router for Ortomapas CRUD, file upload, tile serving, and spatial queries.
"""

import io
import logging
import os
from datetime import datetime
from typing import Optional

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.vrt import WarpedVRT
from rasterio.windows import from_bounds
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from PIL import Image

from backend.config import DATA_DIR, ORTOMAPAS_DIR, THUMBNAILS_DIR
from backend.database.connection import get_connection
from backend.utils.file_manager import save_upload, get_file_size_mb
from backend.utils.geo_utils import get_raster_info, get_raster_bounds
from backend.utils.thumbnail import generate_thumbnail

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ortomapas/spatial")
async def spatial_query(
    norte: float = Query(..., description="North latitude"),
    sul: float = Query(..., description="South latitude"),
    leste: float = Query(..., description="East longitude"),
    oeste: float = Query(..., description="West longitude"),
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
                ORDER BY criado_em DESC
                """,
                (sul, norte, oeste, leste),
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
):
    """List all ortomapas with optional filters."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM ortomapas WHERE 1=1"
            params = []

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
    except Exception as e:
        logger.error(f"Error listing ortomapas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ortomapas/{ortomapa_id}")
async def get_ortomapa(ortomapa_id: int):
    """Get a single ortomapa by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM ortomapas WHERE id = %s", (ortomapa_id,))
            ortomapa = cursor.fetchone()
            if not ortomapa:
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")
            return ortomapa
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ortomapa {ortomapa_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ortomapas", status_code=201)
async def create_ortomapa(data: dict):
    """Create ortomapa metadata record."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            projeto_id = data.get("projeto_id")
            if not projeto_id:
                raise HTTPException(
                    status_code=400, detail="Campo 'projeto_id' e obrigatorio"
                )

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
            conn.commit()
            new_id = cursor.lastrowid

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
):
    """
    Upload a GeoTIFF file and auto-extract metadata (bbox, resolution, size)
    using rasterio.
    """
    filepath = None
    try:
        # Save uploaded file
        filepath = await save_upload(file, ORTOMAPAS_DIR)

        # Extract raster metadata
        info = get_raster_info(filepath)
        north, south, east, west = get_raster_bounds(filepath)
        size_mb = get_file_size_mb(filepath)

        # Calculate resolution in cm (approximate)
        res_cm = info["resolution"]["x"] * 100  # metres to cm if metric CRS

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
            conn.commit()
            new_id = cursor.lastrowid

            cursor.execute("SELECT * FROM ortomapas WHERE id = %s", (new_id,))
            ortomapa = cursor.fetchone()

        return {
            "ortomapa": ortomapa,
            "raster_info": info,
            "file_size_mb": round(size_mb, 2),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading ortomapa: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ortomapas/{ortomapa_id}")
async def update_ortomapa(ortomapa_id: int, data: dict):
    """Update an existing ortomapa."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM ortomapas WHERE id = %s", (ortomapa_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")

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
async def delete_ortomapa(ortomapa_id: int):
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

            cursor.execute("DELETE FROM ortomapas WHERE id = %s", (ortomapa_id,))
            conn.commit()

        # Optionally remove the file
        arquivo = ortomapa.get("caminho_arquivo")
        if arquivo and os.path.exists(arquivo):
            os.remove(arquivo)
            logger.info(f"Removed file: {arquivo}")

        return {"message": "Ortomapa deletado com sucesso", "id": ortomapa_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ortomapa {ortomapa_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ortomapas/{ortomapa_id}/tile/{z}/{x}/{y}.png")
async def get_tile(ortomapa_id: int, z: int, x: int, y: int):
    """
    Serve a 256x256 raster tile from the ortomapa GeoTIFF using rasterio.
    Uses TMS tiling scheme.
    """
    import math

    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT caminho_arquivo FROM ortomapas WHERE id = %s", (ortomapa_id,)
            )
            ortomapa = cursor.fetchone()
            if not ortomapa:
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")

            filepath = ortomapa.get("caminho_arquivo")
            if filepath and not os.path.isabs(filepath):
                filepath = os.path.join(DATA_DIR, filepath)
            if not filepath or not os.path.exists(filepath):
                raise HTTPException(status_code=404, detail="Arquivo GeoTIFF nao encontrado")

        # Calculate XYZ tile bounds directly in Web Mercator (EPSG:3857).
        n = 2 ** z
        world = 20037508.342789244
        tile_span = (2 * world) / n
        tile_left = -world + x * tile_span
        tile_right = tile_left + tile_span
        tile_top = world - y * tile_span
        tile_bottom = tile_top - tile_span

        tile_size = 256

        with rasterio.open(filepath) as source:
          with WarpedVRT(source, crs="EPSG:3857", resampling=Resampling.bilinear) as dataset:
            # Check if tile intersects raster bounds
            raster_bounds = dataset.bounds
            if (
                tile_right < raster_bounds.left
                or tile_left > raster_bounds.right
                or tile_top < raster_bounds.bottom
                or tile_bottom > raster_bounds.top
            ):
                # Return transparent tile
                img = Image.new("RGBA", (tile_size, tile_size), (0, 0, 0, 0))
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                return StreamingResponse(buf, media_type="image/png")

            # Clamp window to raster bounds
            win_left = max(tile_left, raster_bounds.left)
            win_bottom = max(tile_bottom, raster_bounds.bottom)
            win_right = min(tile_right, raster_bounds.right)
            win_top = min(tile_top, raster_bounds.top)

            window = from_bounds(
                win_left, win_bottom, win_right, win_top, dataset.transform
            )

            # Read the window
            out_width = max(1, int(window.width))
            out_height = max(1, int(window.height))
            # Limit to reasonable sizes to avoid OOM
            out_width = min(out_width, tile_size * 4)
            out_height = min(out_height, tile_size * 4)

            band_count = dataset.count
            if band_count >= 3:
                data = dataset.read(
                    [1, 2, 3],
                    window=window,
                    out_shape=(3, out_height, out_width),
                )
                img_array = np.transpose(data, (1, 2, 0))
            else:
                data = dataset.read(
                    1,
                    window=window,
                    out_shape=(out_height, out_width),
                )
                img_array = np.stack([data, data, data], axis=-1)

            # Handle nodata
            nodata = dataset.nodata
            if nodata is not None:
                mask = np.all(img_array == nodata, axis=-1) if img_array.ndim == 3 else (img_array == nodata)
            else:
                mask = None

            # Normalize to uint8
            if img_array.dtype != np.uint8:
                arr_min = np.nanmin(img_array)
                arr_max = np.nanmax(img_array)
                if arr_max > arr_min:
                    img_array = (
                        (img_array - arr_min) / (arr_max - arr_min) * 255
                    ).astype(np.uint8)
                else:
                    img_array = np.zeros_like(img_array, dtype=np.uint8)

            # Create image with alpha channel
            if mask is not None:
                alpha = np.where(mask, 0, 255).astype(np.uint8)
                if img_array.ndim == 3:
                    rgba = np.dstack([img_array, np.expand_dims(alpha, -1)])
                else:
                    rgba = np.dstack(
                        [img_array, img_array, img_array, np.expand_dims(alpha, -1)]
                    )
                img = Image.fromarray(rgba, mode="RGBA")
            else:
                img = Image.fromarray(img_array, mode="RGB")

            # Resize to 256x256
            img = img.resize((tile_size, tile_size), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return StreamingResponse(buf, media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating tile z={z} x={x} y={y} for ortomapa {ortomapa_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
