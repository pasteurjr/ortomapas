"""Queue workers for the existing RGB-change and elevation-volume use cases."""
from __future__ import annotations

import json
import math
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import rasterio
from psycopg2.extras import Json

from backend.config import ANALISES_DIR
from backend.database.connection import get_connection
from backend.tools import change_detection, raster_analysis, volumetry
from backend.utils.analysis_products import publish_rgb_change, publish_terrain
from backend.utils.resource_access import data_path, tool_context


class QueuedChangeVolumeAgent:
    """Execute a queued change or volume request and publish its catalog product."""

    def execute(self, task: dict) -> dict:
        started = perf_counter()
        params = task.get("parametros") or {}
        if isinstance(params, str):
            params = json.loads(params)
        params = dict(params)
        analysis_id = int(params.pop("_analysis_id"))
        project_id = int(params.pop("_project_id"))
        user_id = int(params.pop("_user_id"))
        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM ortomapas WHERE id=%s", (task["ortomapa_id"],))
            after_or_surface = cur.fetchone()
            cur.execute("SELECT * FROM analises WHERE id=%s AND projeto_id=%s", (analysis_id, project_id))
            analysis = cur.fetchone()
            before = None
            if params.get("operation") == "rgb_change":
                cur.execute("SELECT * FROM ortomapas WHERE id=%s", (params.get("reference_id"),))
                before = cur.fetchone()
        if not analysis or not after_or_surface or after_or_surface["projeto_id"] != project_id:
            raise ValueError("Produto ou análise não pertence ao projeto da tarefa")

        project_dir = Path(ANALISES_DIR) / "projetos" / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        context = tool_context.set((user_id, project_id))
        output = project_dir / f"queue_{analysis_id}_{uuid4().hex[:10]}.tif"
        try:
            operation = params.get("operation")
            if operation == "rgb_change":
                if not before or before["projeto_id"] != project_id:
                    raise ValueError("Ortomosaico de referência ausente ou fora do projeto")
                if before["id"] == after_or_surface["id"]:
                    raise ValueError("Selecione dois ortomosaicos distintos")
                for source in (before, after_or_surface):
                    if str(source.get("tipo", "")).lower() not in {"ortomosaico", "rgb", "multispectral"}:
                        raise ValueError("Mudança RGB exige dois ortomosaicos compatíveis")
                first, second = data_path(before["caminho_arquivo"]), data_path(after_or_surface["caminho_arquivo"])
                with rasterio.open(first) as r1, rasterio.open(second) as r2:
                    if min(r1.count, r2.count) < 3 or not r1.crs or not r2.crs:
                        raise ValueError("Os dois rasters precisam ter RGB e CRS")
                    if not r1.crs.is_projected or not r2.crs.is_projected:
                        raise ValueError("Mudança RGB exige CRS projetado")
                    if str(before.get("tipo", "")).lower() != str(after_or_surface.get("tipo", "")).lower():
                        raise ValueError("Compare produtos do mesmo tipo")
                    from pyproj import CRS
                    from rasterio.warp import transform_bounds
                    from shapely.geometry import box
                    for crs in (CRS.from_user_input(r1.crs), CRS.from_user_input(r2.crs)):
                        if not crs.axis_info or abs(float(crs.axis_info[0].unit_conversion_factor) - 1.0) > 1e-9:
                            raise ValueError("O CRS deve usar metros para calcular a área alterada")
                    b1 = transform_bounds(r1.crs, "EPSG:4326", *r1.bounds)
                    b2 = transform_bounds(r2.crs, "EPSG:4326", *r2.bounds)
                    if not box(*b1).intersection(box(*b2)).area:
                        raise ValueError("Os ortomosaicos não possuem área de sobreposição")
                    sample = r1.read((1, 2, 3), out_shape=(3, min(512, r1.height), min(512, r1.width)))
                    scale = float(__import__("numpy").iinfo(r1.dtypes[0]).max) if r1.dtypes[0].startswith(("uint", "int")) else (1.0 if float(sample.max(initial=0)) <= 1 else 255.0)
                threshold = float(params.get("change_threshold", 0.15))
                if not math.isfinite(threshold) or not 0 <= threshold <= 1:
                    raise ValueError("Limiar RGB deve estar entre 0 e 1")
                raw_threshold = threshold * scale
                change_detection.detect_changes(str(first), str(second), str(output), threshold=raw_threshold)
                stats = raster_analysis.raster_statistics(str(output))
                stats["band_1"].update(change_detection.change_statistics(str(output)))
                public_params = {"threshold": threshold, "reference_id": before["id"], "method": "mean_absolute_rgb_difference"}
                published, comparison_id = publish_rgb_change(before, after_or_surface, str(output), stats, public_params, raw_threshold,
                                                               analysis_id=analysis_id, elapsed_seconds=round(perf_counter()-started, 2))
                return {"analise_id": analysis_id, "operation": operation, "statistics": stats["band_1"],
                        "comparacao_id": comparison_id, "status": published.get("status")}

            if operation == "volume":
                if str(after_or_surface.get("tipo", "")).lower() not in {"dsm", "dtm"}:
                    raise ValueError("Volume exige DSM ou DTM")
                reference = float(params.get("reference_elevation"))
                if not math.isfinite(reference):
                    raise ValueError("Cota de referência inválida")
                result = volumetry.calc_volume(str(data_path(after_or_surface["caminho_arquivo"])), reference, str(output))
                stats = raster_analysis.raster_statistics(str(output))
                stats["band_1"].update({k: v for k, v in result.items() if isinstance(v, (int, float)) and not isinstance(v, bool)})
                published = publish_terrain(after_or_surface, "volume", str(output), stats,
                    {"reference_elevation": reference, "volume_type": params.get("volume_type", "both")},
                    analysis_id=analysis_id, elapsed_seconds=round(perf_counter()-started, 2))
                return {"analise_id": analysis_id, "operation": operation, "statistics": result,
                        "status": published.get("status")}
            raise ValueError("Operação de fila desconhecida")
        except Exception:
            output.unlink(missing_ok=True)
            raise
        finally:
            tool_context.reset(context)
