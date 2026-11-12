"""Queued terrain derivatives and contour vectors for project DSM/DTM rasters."""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from backend.config import ANALISES_DIR
from backend.database.connection import get_connection
from backend.tools import gdal_tools, raster_analysis
from backend.utils.analysis_products import publish_contours, publish_terrain
from backend.utils.contour_products import contour_input, contour_result
from backend.utils.raster_metrics import metric_jacobian
from backend.utils.resource_access import data_path, tool_context

logger = logging.getLogger("agent.terrain_queue")


class QueuedTerrainAnalysisAgent:
    """Compute a supported terrain product and finish the queued analysis row."""

    SUPPORTED_DERIVATIVES = {"slope", "aspect", "hillshade", "contours"}

    def execute(self, task: dict) -> dict:
        started = perf_counter()
        params = task.get("parametros") or {}
        if isinstance(params, str):
            params = json.loads(params)
        params = dict(params)

        analysis_id = int(params.pop("_analysis_id"))
        project_id = int(params.pop("_project_id"))
        user_id = int(params.pop("_user_id"))
        derivative = str(params.get("terrain_type", "slope")).lower()
        if derivative not in self.SUPPORTED_DERIVATIVES:
            raise ValueError("Tipo de terreno nao suportado pela fila")
        if derivative == "contours":
            interval = float(params.get("interval", 5.0))
            if not math.isfinite(interval) or not 0 < interval <= 10000:
                raise ValueError("O intervalo de curvas deve estar entre 0 e 10000 metros")
            params["interval"] = interval
        if derivative == "hillshade":
            azimuth = float(params.get("azimuth", 315))
            altitude = float(params.get("altitude", 45))
            if not math.isfinite(azimuth) or not 0 <= azimuth <= 360:
                raise ValueError("Azimute deve estar entre 0 e 360 graus")
            if not math.isfinite(altitude) or not 0 <= altitude <= 90:
                raise ValueError("Elevacao solar deve estar entre 0 e 90 graus")
            params.update(azimuth=azimuth, altitude=altitude)

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
            raise ValueError("DSM/DTM ou analise enfileirada nao existe no projeto informado")
        if str(source.get("tipo", "")).lower() not in {"dsm", "dtm"}:
            raise ValueError("Declividade e orientacao exigem um DSM ou DTM")

        source_path = data_path(source["caminho_arquivo"])
        output_dir = Path(ANALISES_DIR) / "projetos" / str(project_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        extension = ".geojson" if derivative == "contours" else ".tif"
        output_path = output_dir / f"queue_{derivative}_{analysis_id}_{uuid4().hex[:10]}{extension}"
        context_token = tool_context.set((user_id, project_id))
        try:
            params["terrain_type"] = derivative
            params["source_ortomapa_id"] = source["id"]
            if derivative in {"slope", "aspect"}:
                operation = raster_analysis.calc_slope if derivative == "slope" else raster_analysis.calc_aspect
                operation(str(source_path), str(output_path))
                stats = raster_analysis.raster_statistics(str(output_path))
                elapsed = round(perf_counter() - started, 2)
                published = publish_terrain(
                    source, derivative, str(output_path), stats, params,
                    analysis_id=analysis_id, elapsed_seconds=elapsed,
                )
            elif derivative == "hillshade":
                gdal_tools.hillshade(
                    str(source_path), str(output_path),
                    azimuth=params["azimuth"], altitude=params["altitude"],
                )
                stats = raster_analysis.raster_statistics(str(output_path))
                elapsed = round(perf_counter() - started, 2)
                published = publish_terrain(
                    source, derivative, str(output_path), stats, params,
                    analysis_id=analysis_id, elapsed_seconds=elapsed,
                )
            else:
                from rasterio import open as raster_open
                with raster_open(source_path) as raster:
                    crs = raster.crs
                    metric_jacobian(raster.crs, raster.transform)
                interval = params["interval"]
                with contour_input(str(source_path), None) as contour_source:
                    gdal_tools.generate_contours(
                        contour_source, str(output_path), interval=interval,
                    )
                metadata = contour_result(str(output_path), crs, interval)
                stats = metadata["stats"]
                elapsed = round(perf_counter() - started, 2)
                published = publish_contours(
                    source, str(output_path), metadata, params,
                    analysis_id=analysis_id, elapsed_seconds=elapsed,
                )
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
        finally:
            tool_context.reset(context_token)

        logger.info("Queued terrain analysis %s completed for task %s", analysis_id, task["id"])
        return {
            "analise_id": analysis_id,
            "output_path": str(output_path),
            "operation": derivative,
            "statistics": stats,
            "elapsed_seconds": round(perf_counter() - started, 2),
            "status": published.get("status"),
        }
