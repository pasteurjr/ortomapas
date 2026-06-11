"""
Router for Projetos (projects) CRUD and related queries.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from backend.database.connection import get_connection

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/projetos/search")
async def search_projetos(q: str = Query(..., min_length=1, description="Search term")):
    """Fulltext search across projetos (nome, descricao, area_estudo)."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            search_term = f"%{q}%"
            cursor.execute(
                """
                SELECT * FROM projetos
                WHERE nome LIKE %s
                   OR descricao LIKE %s
                   OR area_estudo LIKE %s
                ORDER BY criado_em DESC
                """,
                (search_term, search_term, search_term),
            )
            rows = cursor.fetchall()
            return {"total": len(rows), "projetos": rows}
    except Exception as e:
        logger.error(f"Error searching projetos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projetos")
async def list_projetos(
    status: Optional[str] = Query(None, description="Filter by status"),
    area_estudo: Optional[str] = Query(None, description="Filter by area de estudo"),
):
    """List all projetos with optional filters."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM projetos WHERE 1=1"
            params = []

            if status:
                query += " AND status = %s"
                params.append(status)
            if area_estudo:
                query += " AND area_estudo LIKE %s"
                params.append(f"%{area_estudo}%")

            query += " ORDER BY criado_em DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return {"total": len(rows), "projetos": rows}
    except Exception as e:
        logger.error(f"Error listing projetos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projetos/{projeto_id}")
async def get_projeto(projeto_id: int):
    """Get a single projeto by ID with related counts."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM projetos WHERE id = %s", (projeto_id,))
            projeto = cursor.fetchone()
            if not projeto:
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

            # Related counts
            cursor.execute(
                "SELECT COUNT(*) as total FROM voos WHERE projeto_id = %s", (projeto_id,)
            )
            projeto["total_voos"] = cursor.fetchone()["total"]

            cursor.execute(
                "SELECT COUNT(*) as total FROM ortomapas WHERE projeto_id = %s",
                (projeto_id,),
            )
            projeto["total_ortomapas"] = cursor.fetchone()["total"]

            cursor.execute(
                """
                SELECT COUNT(*) as total FROM analises a
                JOIN ortomapas o ON a.ortomapa_id = o.id
                WHERE o.projeto_id = %s
                """,
                (projeto_id,),
            )
            projeto["total_analises"] = cursor.fetchone()["total"]

            return projeto
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting projeto {projeto_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projetos", status_code=201)
async def create_projeto(data: dict):
    """Create a new projeto."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            nome = data.get("nome")
            if not nome:
                raise HTTPException(status_code=400, detail="Campo 'nome' e obrigatorio")

            cursor.execute(
                """
                INSERT INTO projetos (nome, descricao, area_estudo, status, criado_em)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    nome,
                    data.get("descricao", ""),
                    data.get("area_estudo", ""),
                    data.get("status", "ativo"),
                    datetime.utcnow(),
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid

            cursor.execute("SELECT * FROM projetos WHERE id = %s", (new_id,))
            projeto = cursor.fetchone()
            return projeto
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating projeto: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projetos/{projeto_id}")
async def update_projeto(projeto_id: int, data: dict):
    """Update an existing projeto."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM projetos WHERE id = %s", (projeto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

            fields = []
            params = []
            for field in ["nome", "descricao", "area_estudo", "status"]:
                if field in data:
                    fields.append(f"{field} = %s")
                    params.append(data[field])

            if not fields:
                raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

            fields.append("atualizado_em = %s")
            params.append(datetime.utcnow())
            params.append(projeto_id)

            cursor.execute(
                f"UPDATE projetos SET {', '.join(fields)} WHERE id = %s", params
            )
            conn.commit()

            cursor.execute("SELECT * FROM projetos WHERE id = %s", (projeto_id,))
            return cursor.fetchone()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating projeto {projeto_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projetos/{projeto_id}")
async def delete_projeto(projeto_id: int):
    """Delete a projeto."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM projetos WHERE id = %s", (projeto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

            cursor.execute("DELETE FROM projetos WHERE id = %s", (projeto_id,))
            conn.commit()
            return {"message": "Projeto deletado com sucesso", "id": projeto_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting projeto {projeto_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projetos/{projeto_id}/ortomapas")
async def list_ortomapas_by_projeto(projeto_id: int):
    """List all ortomapas for a specific projeto."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM projetos WHERE id = %s", (projeto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Projeto nao encontrado")

            cursor.execute(
                """
                SELECT * FROM ortomapas
                WHERE projeto_id = %s
                ORDER BY criado_em DESC
                """,
                (projeto_id,),
            )
            rows = cursor.fetchall()
            return {"total": len(rows), "ortomapas": rows}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing ortomapas for projeto {projeto_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
