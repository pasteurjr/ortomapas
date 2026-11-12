"""Queue adapter for RGB K-Means analyses submitted from AnalysisForm."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from backend.config import ANALISES_DIR
from backend.database.connection import get_connection
from backend.tools import raster_analysis, segmentation
from backend.utils.analysis_products import publish_image_analysis
from backend.utils.resource_access import data_path, tool_context

logger = logging.getLogger("agent.classification_queue")


class QueuedClassificationAgent:
    """Run the same RGB K-Means pipeline as the GIS tools and update its queued row."""

    def execute(self, task: dict) -> dict:
        started = perf_counter()
        params = task.get("parametros") or {}
        if isinstance(params, str):
            params = json.loads(params)
        params = dict(params)

        analysis_id = int(params.pop("_analysis_id"))
        project_id = int(params.pop("_project_id"))
        user_id = int(params.pop("_user_id"))
        algorithm = str(params.pop("algorithm", "kmeans")).lower()
        n_clusters = int(params.pop("n_clusters", params.pop("n_classes", 5)))
        if algorithm != "kmeans":
            raise ValueError("A fila aceita somente o algoritmo K-Means nesta etapa")
        if not 2 <= n_clusters <= 12:
            raise ValueError("O numero de grupos deve estar entre 2 e 12")

        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM ortomapas WHERE id=%s", (task["ortomapa_id"],))
            source = cur.fetchone()
            cur.execute("SELECT id FROM analises WHERE id=%s AND ortomapa_id=%s AND projeto_id=%s",
                        (analysis_id, task["ortomapa_id"], project_id))
            target = cur.fetchone()
        if not source or source["projeto_id"] != project_id or not target:
            raise ValueError("Ortomapa ou analise enfileirada nao existe no projeto informado")
        if str(source.get("tipo", "")).lower() not in {"ortomosaico", "rgb", "multispectral"}:
            raise ValueError("Classificacao K-Means exige um ortomosaico RGB")

        source_path = data_path(source["caminho_arquivo"])
        output_path = Path(ANALISES_DIR) / f"class_queue_{analysis_id}_{uuid4().hex[:10]}.tif"
        started_context = tool_context.set((user_id, project_id))
        try:
            details = segmentation.segment_ortomapa(
                str(source_path), str(output_path), n_clusters=n_clusters
            )
            stats = raster_analysis.raster_statistics(str(output_path))
            params.update({
                "algorithm": "kmeans",
                "n_clusters": n_clusters,
                "source_ortomapa_id": source["id"],
            })
            elapsed=round(perf_counter()-started,2)
            analysis = publish_image_analysis(
                source, "classification", str(output_path), stats, params,
                details=details, analysis_id=analysis_id, elapsed_seconds=elapsed,
            )
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
        finally:
            tool_context.reset(started_context)

        logger.info("Queued classification %s complete for task %s", analysis_id, task["id"])
        return {
            "analise_id": analysis_id,
            "output_path": str(output_path),
            "algorithm": "kmeans",
            "n_clusters": n_clusters,
            "valid_pixels": details["total_valid_pixels"],
            "sample_pixels": details["sample_pixels"],
            "elapsed_seconds": round(perf_counter() - started, 2),
        }
