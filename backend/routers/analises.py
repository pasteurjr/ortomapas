"""
Router for Analises (analyses) CRUD and result serving.
"""

import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.config import ANALISES_DIR
from backend.database.connection import get_connection

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analises")
async def list_analises(
    ortomapa_id: Optional[int] = Query(None, description="Filter by ortomapa_id"),
    projeto_id: Optional[int] = Query(None, description="Filter by projeto_id"),
    tipo_analise: Optional[str] = Query(None, description="Filter by tipo_analise"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """List all analises with optional filters."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            query = "SELECT * FROM analises WHERE 1=1"
            params = []

            if ortomapa_id is not None:
                query += " AND ortomapa_id = %s"
                params.append(ortomapa_id)
            if projeto_id is not None:
                query += " AND projeto_id = %s"
                params.append(projeto_id)
            if tipo_analise:
                query += " AND tipo_analise = %s"
                params.append(tipo_analise)
            if status:
                query += " AND status = %s"
                params.append(status)

            query += " ORDER BY criado_em DESC"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return {"total": len(rows), "analises": rows}
    except Exception as e:
        logger.error(f"Error listing analises: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analises/{analise_id}")
async def get_analise(analise_id: int):
    """Get a single analise by ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT * FROM analises WHERE id = %s", (analise_id,))
            analise = cursor.fetchone()
            if not analise:
                raise HTTPException(status_code=404, detail="Analise nao encontrada")
            return analise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analise {analise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analises", status_code=201)
async def create_analise(data: dict):
    """
    Create a new analise and optionally queue it as an agent task.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            ortomapa_id = data.get("ortomapa_id")
            if not ortomapa_id:
                raise HTTPException(
                    status_code=400, detail="Campo 'ortomapa_id' e obrigatorio"
                )

            tipo_analise = data.get("tipo_analise")
            if not tipo_analise:
                raise HTTPException(
                    status_code=400, detail="Campo 'tipo_analise' e obrigatorio"
                )

            # Verify ortomapa exists
            cursor.execute("SELECT id FROM ortomapas WHERE id = %s", (ortomapa_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Ortomapa nao encontrado")

            cursor.execute(
                """
                INSERT INTO analises (
                    ortomapa_id, tipo_analise, parametros, status,
                    arquivo_resultado, observacoes, criado_em
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    ortomapa_id,
                    tipo_analise,
                    data.get("parametros", "{}"),
                    data.get("status", "pendente"),
                    data.get("arquivo_resultado", ""),
                    data.get("observacoes", ""),
                    datetime.utcnow(),
                ),
            )
            conn.commit()
            new_id = cursor.lastrowid

            # Optionally queue as agent task
            queue_task = data.get("queue_task", False)
            if queue_task:
                try:
                    cursor.execute(
                        """
                        INSERT INTO tarefas_agente (
                            tipo_tarefa, referencia_id, parametros, status, criado_em
                        ) VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            f"analise_{tipo_analise}",
                            new_id,
                            data.get("parametros", "{}"),
                            "pendente",
                            datetime.utcnow(),
                        ),
                    )
                    conn.commit()
                    logger.info(f"Agent task queued for analise {new_id}")
                except Exception as te:
                    logger.warning(f"Could not queue agent task: {te}")

            cursor.execute("SELECT * FROM analises WHERE id = %s", (new_id,))
            analise = cursor.fetchone()
            return analise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating analise: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analises/{analise_id}/resultado")
async def get_analise_resultado(analise_id: int):
    """Serve the result file of an analise."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM analises WHERE id = %s", (analise_id,)
            )
            analise = cursor.fetchone()
            if not analise:
                raise HTTPException(status_code=404, detail="Analise nao encontrada")

            arquivo = analise.get("arquivo_resultado")
            if not arquivo or not os.path.exists(arquivo):
                raise HTTPException(
                    status_code=404, detail="Arquivo de resultado nao encontrado"
                )

        filename = os.path.basename(arquivo)
        return FileResponse(
            path=arquivo,
            filename=filename,
            media_type="application/octet-stream",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving resultado for analise {analise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/analises/{analise_id}")
async def delete_analise(analise_id: int):
    """Delete an analise and optionally its result file."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                "SELECT * FROM analises WHERE id = %s", (analise_id,)
            )
            analise = cursor.fetchone()
            if not analise:
                raise HTTPException(status_code=404, detail="Analise nao encontrada")

            cursor.execute("DELETE FROM analises WHERE id = %s", (analise_id,))
            conn.commit()

        # Remove result file if it exists
        arquivo = analise.get("arquivo_resultado")
        if arquivo and os.path.exists(arquivo):
            os.remove(arquivo)
            logger.info(f"Removed result file: {arquivo}")

        return {"message": "Analise deletada com sucesso", "id": analise_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analise {analise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
