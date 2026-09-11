"""
Router for Voos (flights) CRUD operations.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

from backend.database.connection import get_connection
from backend.routers.auth import current_user, require_project_role

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/voos")
async def list_voos(
    projeto_id: Optional[int] = Query(None, description="Filter by projeto_id"),
    user: dict = Depends(current_user),
):
    """List all voos with optional filter by projeto_id."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM voos WHERE 1=1"
            params = []

            if projeto_id is not None:
                require_project_role(projeto_id, user, {"proprietario", "editor", "visualizador"})
                query += " AND projeto_id = %s"
                params.append(projeto_id)

            query += " ORDER BY data_voo DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return {"total": len(rows), "voos": rows}
    except Exception as e:
        logger.error(f"Error listing voos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voos/{voo_id}")
async def get_voo(voo_id: int, user: dict = Depends(current_user)):
    """Get a single voo by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM voos WHERE id = %s", (voo_id,))
            voo = cursor.fetchone()
            if not voo:
                raise HTTPException(status_code=404, detail="Voo nao encontrado")
            require_project_role(voo["projeto_id"], user, {"proprietario", "editor", "visualizador"})
            return voo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting voo {voo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voos", status_code=201)
async def create_voo(data: dict, user: dict = Depends(current_user)):
    """Create a new voo."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            projeto_id = data.get("projeto_id")
            if not projeto_id:
                raise HTTPException(
                    status_code=400, detail="Campo 'projeto_id' e obrigatorio"
                )
            require_project_role(projeto_id, user, {"proprietario", "editor"})

            # Verify projeto exists
            cursor.execute("SELECT id FROM projetos WHERE id = %s", (projeto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

            cursor.execute(
                """
                INSERT INTO voos (
                    projeto_id, data_voo, local_decolagem_lat, local_decolagem_lon,
                    altitude_voo_m, velocidade_ms,
                    sobreposicao_frontal, sobreposicao_lateral, num_fotos,
                    resolucao_foto, formato_foto, gsd_cm,
                    area_coberta_ha, num_baterias, tipo_bateria,
                    condicoes_vento, condicoes_ceu, temperatura_c,
                    app_voo, observacoes, criado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    projeto_id,
                    data.get("data_voo"),
                    data.get("local_decolagem_lat"),
                    data.get("local_decolagem_lon"),
                    data.get("altitude_voo_m"),
                    data.get("velocidade_ms"),
                    data.get("sobreposicao_frontal"),
                    data.get("sobreposicao_lateral"),
                    data.get("num_fotos"),
                    data.get("resolucao_foto", "48MP"),
                    data.get("formato_foto", "JPEG"),
                    data.get("gsd_cm"),
                    data.get("area_coberta_ha"),
                    data.get("num_baterias"),
                    data.get("tipo_bateria", "standard"),
                    data.get("condicoes_vento"),
                    data.get("condicoes_ceu"),
                    data.get("temperatura_c"),
                    data.get("app_voo", "Litchi Pilot"),
                    data.get("observacoes", ""),
                    datetime.utcnow(),
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid

            cursor.execute("SELECT * FROM voos WHERE id = %s", (new_id,))
            voo = cursor.fetchone()
            return voo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating voo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/voos/{voo_id}")
async def update_voo(voo_id: int, data: dict, user: dict = Depends(current_user)):
    """Update an existing voo."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM voos WHERE id = %s", (voo_id,))
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Voo nao encontrado")
            require_project_role(existing["projeto_id"], user, {"proprietario", "editor"})

            updatable = [
                "data_voo", "drone", "camera", "altitude_voo",
                "sobreposicao_frontal", "sobreposicao_lateral", "num_fotos",
                "area_coberta_ha", "gsd_cm", "observacoes", "status",
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
            params.append(voo_id)

            cursor.execute(
                f"UPDATE voos SET {', '.join(fields)} WHERE id = %s", params
            )
            conn.commit()

            cursor.execute("SELECT * FROM voos WHERE id = %s", (voo_id,))
            return cursor.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating voo {voo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/voos/{voo_id}")
async def delete_voo(voo_id: int, user: dict = Depends(current_user)):
    """Delete a voo."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM voos WHERE id = %s", (voo_id,))
            existing = cursor.fetchone()
            if not existing:
                raise HTTPException(status_code=404, detail="Voo nao encontrado")
            require_project_role(existing["projeto_id"], user, {"proprietario"})

            cursor.execute("DELETE FROM voos WHERE id = %s", (voo_id,))
            conn.commit()
            return {"message": "Voo deletado com sucesso", "id": voo_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting voo {voo_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
