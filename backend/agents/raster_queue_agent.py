"""Queue adapter for RGB vegetation-index analyses requested through the UI."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from backend.config import ANALISES_DIR
from backend.database.connection import get_connection
from backend.tools import raster_analysis
from backend.utils.analysis_products import publish_image_analysis
from backend.utils.resource_access import data_path, tool_context

logger = logging.getLogger("agent.raster_queue")


class QueuedRasterAnalysisAgent:
    """Process a queued visible-band vegetation index and publish its raster."""

    SUPPORTED_INDICES = {"VARI", "TGI", "EXG", "GLI"}

    def execute(self, task: dict) -> dict:
        started = perf_counter()
        params = task.get("parametros") or {}
        if isinstance(params, str):
            params = json.loads(params)
        params = dict(params)

        analysis_id = int(params.pop("_analysis_id"))
        project_id = int(params.pop("_project_id"))
        user_id = int(params.pop("_user_id"))
        index_name = str(params.get("index_name", "VARI")).upper()
        if index_name not in self.SUPPORTED_INDICES:
            raise ValueError(f"Indice RGB nao suportado: {index_name}")

        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM ortomapas WHERE id=%s", (task["ortomapa_id"],))
            source = cur.fetchone()
            cur.execute(
                "SELECT id FROM analises WHERE id=%s AND ortomapa_id=%s AND projeto_id=%s",
                (analysis_id, task["ortomapa_id"], project_id),
            )
            target = cur.fetchone()
        if not source or source["projeto_id"] != project_id or not target:
            raise ValueError("Ortomapa ou analise enfileirada nao existe no projeto informado")
        if str(source.get("tipo", "")).lower() not in {"ortomosaico", "rgb", "multispectral"}:
            raise ValueError("Indice de vegetacao RGB exige um ortomosaico")

        source_path = data_path(source["caminho_arquivo"])
        output_dir = Path(ANALISES_DIR) / "projetos" / str(project_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"queue_vegetation_{analysis_id}_{uuid4().hex[:10]}.tif"
        context_token = tool_context.set((user_id, project_id))
        try:
            raster_analysis.calc_vegetation_index(
                str(source_path), str(output_path), index_name=index_name
            )
            stats = raster_analysis.raster_statistics(str(output_path))
            params["index_name"] = index_name
            params["source_ortomapa_id"] = source["id"]
            elapsed = round(perf_counter() - started, 2)
            published = publish_image_analysis(
                source,
                "vegetation",
                str(output_path),
                stats,
                params,
                analysis_id=analysis_id,
                elapsed_seconds=elapsed,
            )
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
        finally:
            tool_context.reset(context_token)

        logger.info("Queued vegetation analysis %s completed for task %s", analysis_id, task["id"])
        return {
            "analise_id": analysis_id,
            "output_path": str(output_path),
            "index_name": index_name,
            "statistics": stats,
            "elapsed_seconds": round(perf_counter() - started, 2),
            "status": published.get("status"),
        }
