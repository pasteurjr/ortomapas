"""Queued D8 drainage-network extraction from a project DSM/DTM."""
from __future__ import annotations

import json
import logging
import math
import tempfile
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import rasterio

from backend.config import ANALISES_DIR
from backend.database.connection import get_connection
from backend.tools import hydrology
from backend.utils.analysis_products import publish_hydrology
from backend.utils.raster_metrics import metric_jacobian
from backend.utils.resource_access import data_path, tool_context

logger = logging.getLogger("agent.hydrology_queue")


class QueuedHydrologyAnalysisAgent:
    """Prepare a bounded DEM grid and publish a D8 stream network."""

    def execute(self, task: dict) -> dict:
        started = perf_counter()
        params = task.get("parametros") or {}
        if isinstance(params, str):
            params = json.loads(params)
        params = dict(params)
        analysis_id = int(params.pop("_analysis_id"))
        project_id = int(params.pop("_project_id"))
        user_id = int(params.pop("_user_id"))
        hydro_type = str(params.get("hydro_type", "")).lower()
        if hydro_type not in {"flow_direction", "flow_accumulation", "twi", "drainage", "watershed"}:
            raise ValueError("Operacao hidrologica nao suportada pela fila")
        minimum_area_m2 = float(params.get("minimum_area_m2", 1000))
        minimum_strahler_order = int(params.get("minimum_strahler_order", 1))
        if hydro_type == "drainage" and (not math.isfinite(minimum_area_m2) or not 1 <= minimum_area_m2 <= 1_000_000_000):
            raise ValueError("A area contribuinte minima deve estar entre 1 e 1000000000 m²")
        if hydro_type == "drainage" and not 1 <= minimum_strahler_order <= 12:
            raise ValueError("A ordem de Strahler minima deve estar entre 1 e 12")
        outlet = params.get("outlet")
        snap_radius_m = float(params.get("snap_radius_m", 5))
        hydrography_path = params.get("hydrography_path")
        burn_depth_m = float(params.get("burn_depth_m", 0.05))
        if not math.isfinite(burn_depth_m) or not 0 <= burn_depth_m <= 20:
            raise ValueError("A profundidade de condicionamento deve estar entre 0 e 20 m")
        if hydro_type == "watershed":
            if not isinstance(outlet, dict):
                raise ValueError("Selecione um exutorio no mapa antes de enfileirar a bacia")
            lat = float(outlet.get("lat", float("nan")))
            lon = float(outlet.get("lng", outlet.get("lon", float("nan"))))
            if not math.isfinite(lat) or not math.isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
                raise ValueError("Exutorio deve conter latitude/longitude WGS84 validas")
            if not math.isfinite(snap_radius_m) or not 0 <= snap_radius_m <= 1000:
                raise ValueError("Raio de ajuste do exutorio deve estar entre 0 e 1000 metros")
            outlet = {"lat": lat, "lon": lon}
        max_dimension = int(params.get("max_dimension", 512 if hydro_type == "watershed" else 256))
        if not 128 <= max_dimension <= 4096:
            raise ValueError("A dimensao de trabalho deve estar entre 128 e 4096 pixels")

        with get_connection() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT * FROM ortomapas WHERE id=%s", (task["ortomapa_id"],))
            source = cur.fetchone()
            cur.execute("SELECT id FROM analises WHERE id=%s AND ortomapa_id=%s AND projeto_id=%s",
                        (analysis_id, task["ortomapa_id"], project_id))
            target = cur.fetchone()
        if not source or source["projeto_id"] != project_id or not target:
            raise ValueError("DSM/DTM ou analise enfileirada nao existe no projeto informado")
        if str(source.get("tipo", "")).lower() not in {"dsm", "dtm"}:
            raise ValueError("A rede de drenagem exige um DSM ou DTM")

        source_path = data_path(source["caminho_arquivo"])
        with rasterio.open(source_path) as raster:
            if not raster.crs or not raster.crs.is_projected:
                raise ValueError("A hidrologia exige DSM/DTM projetado em unidades metricas")
            metric_jacobian(raster.crs, raster.transform)

        output_dir = Path(ANALISES_DIR) / "projetos" / str(project_id)
        output_dir.mkdir(parents=True, exist_ok=True)
        extension = "geojson" if hydro_type == "drainage" else "tif"
        output_path = output_dir / f"queue_{hydro_type}_{analysis_id}_{uuid4().hex[:10]}.{extension}"
        context_token = tool_context.set((user_id, project_id))
        try:
            with tempfile.TemporaryDirectory(prefix="ortomapas_hydro_queue_") as folder:
                work = str(Path(folder) / "dem.tif")
                filled = str(Path(folder) / "filled.tif")
                conditioned = str(Path(folder) / "conditioned.tif")
                direction = str(Path(folder) / "direction.tif")
                accumulation = str(Path(folder) / "accumulation.tif")
                grid = hydrology.prepare_dem(str(source_path), work, max_dimension=max_dimension)
                hydrology.fill_sinks(work, filled)
                conditioning = None
                routing_surface = filled
                if hydro_type == "watershed" and hydrography_path:
                    conditioning = hydrology.condition_dem_with_hydrography(
                        filled, str(data_path(hydrography_path)), conditioned, burn_depth_m)
                    routing_surface = conditioned
                hydrology.flow_direction(routing_surface, direction)
                hydrology.flow_accumulation(direction, accumulation)
                if hydro_type == "flow_direction":
                    hydrology.flow_direction(filled, str(output_path))
                    with rasterio.open(output_path) as result_ds:
                        values = result_ds.read(1, masked=True).compressed()
                    result = {"valid_cells": int(values.size), "direction_codes": sorted(map(int, set(values.tolist()))),
                              "working_grid": grid}
                elif hydro_type == "flow_accumulation":
                    hydrology.flow_direction(filled, direction)
                    hydrology.flow_accumulation(direction, str(output_path))
                    with rasterio.open(output_path) as result_ds:
                        values = result_ds.read(1, masked=True).compressed()
                    result = {"valid_cells": int(values.size), "minimum_cells": int(values.min()),
                              "maximum_cells": int(values.max()), "working_grid": grid}
                elif hydro_type == "twi":
                    hydrology.flow_direction(filled, direction)
                    hydrology.flow_accumulation(direction, accumulation)
                    slope = str(Path(folder) / "slope.tif")
                    from backend.tools import raster_analysis
                    raster_analysis.calc_slope(filled, slope)
                    hydrology.calc_twi(slope, accumulation, str(output_path))
                    from backend.tools.raster_analysis import raster_statistics
                    result = {**raster_statistics(str(output_path))["band_1"], "working_grid": grid}
                elif hydro_type == "drainage":
                    result = hydrology.extract_stream_lines(
                        accumulation, direction, str(output_path), minimum_area_m2, minimum_strahler_order)
                else:
                    from pyproj import Transformer
                    with rasterio.open(work) as dem:
                        forward = Transformer.from_crs(4326, dem.crs, always_xy=True)
                        reverse = Transformer.from_crs(dem.crs, 4326, always_xy=True)
                    outlet_x, outlet_y = forward.transform(outlet["lon"], outlet["lat"])
                    snapped = hydrology.snap_pour_point(accumulation, outlet_x, outlet_y, snap_radius_m)
                    result = hydrology.watershed_from_flow(direction, str(output_path), snapped["row"], snapped["col"])
                    snapped_lon, snapped_lat = reverse.transform(*snapped["snapped_xy"])
                    result.update(requested_outlet={"lat": outlet["lat"], "lon": outlet["lon"]},
                                  snapped_outlet={"lat": snapped_lat, "lon": snapped_lon,
                                                  "distance_m": snapped["snap_distance_m"],
                                                  "accumulation_cells": snapped["accumulation_cells"],
                                                  "radius_m": snap_radius_m,
                                                  "strategy": snapped["snap_strategy"]})
                    result["hydrography_conditioning"] = conditioning
                result["working_grid"] = grid
            params.update(hydro_type=hydro_type, max_dimension=max_dimension, source_ortomapa_id=source["id"])
            if hydro_type == "drainage":
                params["minimum_area_m2"] = minimum_area_m2
                params["minimum_strahler_order"] = minimum_strahler_order
            elif hydro_type == "watershed":
                params.update(outlet=outlet, snap_radius_m=snap_radius_m)
            elapsed = round(perf_counter() - started, 2)
            published = publish_hydrology(
                source, {"drainage":"streams","watershed":"watershed"}.get(hydro_type, hydro_type), str(output_path), result, params,
                analysis_id=analysis_id, elapsed_seconds=elapsed,
            )
        except Exception:
            output_path.unlink(missing_ok=True)
            raise
        finally:
            tool_context.reset(context_token)

        logger.info("Queued hydrology analysis %s completed for task %s", analysis_id, task["id"])
        return {"analise_id": analysis_id, "output_path": str(output_path),
                "operation": hydro_type, "statistics": result,
                "elapsed_seconds": round(perf_counter() - started, 2),
                "status": published.get("status")}
