"""Run the application D8 pipeline on public 3DEP and compare with 3DHP.

This benchmark is independent of ODM project #88/DTM #72. It writes all
intermediate products to a temporary directory and performs no DB writes.
"""
from __future__ import annotations

import hashlib
import json
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.crs import CRS
from rasterio.warp import Resampling, calculate_default_transform, reproject
from shapely.geometry import box, mapping, shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from backend.tools import hydrology

EVIDENCE = ROOT / "docs/validacao/ortomapas_conclusao/etapa-09/referencias"
DEM = EVIDENCE / "3dep_aukerman_dem_context.tif"
REFERENCE = EVIDENCE / "3dhp_flowlines_aukerman_context.geojson"
CLIPPED = EVIDENCE / "3dhp_flowlines_3dep_clip.geojson"
RESULT = EVIDENCE / "benchmark_3dep_3dhp_d8.json"
FIGURE = EVIDENCE / "benchmark_3dep_3dhp_d8.png"
CRS_METRIC = "EPSG:32617"
THRESHOLDS_M2 = (10000.0, 50000.0, 100000.0)
TOLERANCES_M = (25.0, 50.0, 100.0)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def features_from_geojson(path: Path, transformer: Transformer, clip):
    data = json.loads(path.read_text(encoding="utf-8"))
    output = []
    for raw in data.get("features", []):
        geom = transform(transformer.transform, shape(raw["geometry"]))
        if clip is not None:
            geom = geom.intersection(clip)
        if not geom.is_empty and geom.length > 0:
            output.append((raw.get("properties", {}), geom))
    return output


def network_metrics(predicted, reference, tolerance):
    if predicted.is_empty or reference.is_empty:
        return {"mean_distance_m": None, "median_distance_m": None,
                "coverage_predicted_pct": None, "coverage_reference_pct": None}
    sample_count = max(1, int(predicted.length))
    distances = [predicted.interpolate(min(predicted.length, i)).distance(reference)
                 for i in range(sample_count + 1)]
    distances.sort()
    return {
        "sample_interval_m": 1.0,
        "sample_count": len(distances),
        "mean_distance_m": sum(distances) / len(distances),
        "median_distance_m": distances[len(distances) // 2],
        "p95_distance_m": distances[min(len(distances) - 1, int(.95 * len(distances)))],
        "coverage_predicted_pct": 100 * predicted.intersection(reference.buffer(tolerance)).length / predicted.length,
        "coverage_reference_pct": 100 * reference.intersection(predicted.buffer(tolerance)).length / reference.length,
    }


def main():
    transform_to_metric = Transformer.from_crs("EPSG:4326", CRS_METRIC, always_xy=True)
    transform_to_wgs84 = Transformer.from_crs(CRS_METRIC, "EPSG:4326", always_xy=True)

    with tempfile.TemporaryDirectory(prefix="ortomapas-3dep-9-5-") as temp:
        temp = Path(temp)
        metric_dem = temp / "3dep_metric.tif"
        working = temp / "working.tif"
        filled = temp / "filled.tif"
        direction = temp / "direction.tif"
        accumulation = temp / "accumulation.tif"

        with rasterio.open(DEM) as source:
            dst_transform, width, height = calculate_default_transform(
                source.crs, CRS.from_string(CRS_METRIC), source.width, source.height, *source.bounds
            )
            profile = source.profile.copy()
            profile.update(crs=CRS_METRIC, transform=dst_transform, width=width,
                           height=height, dtype="float32", count=1, nodata=-9999.0)
            with rasterio.open(metric_dem, "w", **profile) as target:
                reproject(rasterio.band(source, 1), rasterio.band(target, 1),
                          src_transform=source.transform, src_crs=source.crs,
                          dst_transform=dst_transform, dst_crs=CRS_METRIC,
                          resampling=Resampling.bilinear)

        grid = hydrology.prepare_dem(str(metric_dem), str(working), max_dimension=1024)
        hydrology.fill_sinks(str(working), str(filled))
        hydrology.flow_direction(str(filled), str(direction))
        hydrology.flow_accumulation(str(direction), str(accumulation))

        with rasterio.open(working) as ds:
            clip = box(*ds.bounds)
            raster_meta = {"crs": ds.crs.to_string(), "bounds_m": list(ds.bounds),
                           "width": ds.width, "height": ds.height,
                           "pixel_size_m": [abs(ds.transform.a), abs(ds.transform.e)],
                           "working_grid": grid}

        raw_reference = json.loads(REFERENCE.read_text(encoding="utf-8"))
        all_reference = features_from_geojson(REFERENCE, transform_to_metric, clip)
        river_reference = [(p, g) for p, g in all_reference if str(p.get("featuretype")) == "1"]
        pairable_reference = [(p, g) for p, g in river_reference if p.get("streamorder") is not None]
        type_counts = Counter(str(p.get("featuretype")) for p, _ in all_reference)

        clipped_fc = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": props,
             "geometry": mapping(transform(transform_to_wgs84.transform, geom))}
            for props, geom in all_reference
        ]}
        CLIPPED.write_text(json.dumps(clipped_fc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

        results = {}
        geometries_by_threshold = {}
        for threshold in THRESHOLDS_M2:
            out = temp / f"d8_{int(threshold)}.geojson"
            extraction = hydrology.extract_stream_lines(str(accumulation), str(direction),
                                                         str(out), threshold, 1)
            predicted = features_from_geojson(out, transform_to_metric, clip)
            geometries_by_threshold[str(int(threshold))] = predicted
            orders = sorted({int(p.get("ordem_strahler", 0)) for p, _ in predicted}
                            & {int(p["streamorder"]) for p, _ in pairable_reference})
            by_order = {}
            for order in orders:
                pred_class = unary_union([g for p, g in predicted if int(p.get("ordem_strahler", 0)) == order])
                ref_class = unary_union([g for p, g in pairable_reference if int(p["streamorder"]) == order])
                by_order[str(order)] = {
                    "predicted_features": sum(int(p.get("ordem_strahler", 0)) == order for p, _ in predicted),
                    "reference_features": sum(int(p["streamorder"]) == order for p, _ in pairable_reference),
                    "predicted_length_m": float(pred_class.length),
                    "reference_length_m": float(ref_class.length),
                    "tolerances": {str(int(tol)): network_metrics(pred_class, ref_class, tol)
                                   for tol in TOLERANCES_M},
                }
            results[str(int(threshold))] = {
                "minimum_contributing_area_m2": threshold,
                "threshold_cells": extraction["threshold_cells"],
                "predicted_features": extraction["feature_count"],
                "predicted_stream_cells": extraction["stream_cells"],
                "predicted_total_length_m": extraction["total_length_m"],
                "predicted_order_lengths_m": extraction["order_lengths_m"],
                "predicted_orders": sorted({int(p.get("ordem_strahler", 0)) for p, _ in predicted}),
                "reference_orders_type1": sorted({int(p.get("streamorder", 0) or 0) for p, _ in river_reference}),
                "orders_compared": orders,
                "by_order": by_order,
            }

        # Plot the predeclared middle threshold (50,000 m²) and official order/type classes.
        figure, axis = plt.subplots(figsize=(12, 9), dpi=160)
        palette = {1: "#2563eb", 2: "#e11d48", 3: "#16a34a", 4: "#7c3aed", 5: "#d97706", 6: "#0891b2"}
        chosen = geometries_by_threshold["50000"]
        labels = set()
        for props, geom in chosen:
            order = int(props.get("ordem_strahler", 0))
            parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
            for part in parts:
                x, y = part.xy
                label = f"D8 potencial, ordem {order}"
                axis.plot(x, y, color=palette.get(order, "#111827"), linewidth=1.4,
                          label=label if label not in labels else None)
                labels.add(label)
        for props, geom in pairable_reference:
            order = int(props["streamorder"])
            parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
            for part in parts:
                x, y = part.xy
                label = f"USGS 3DHP rio, ordem {order}"
                axis.plot(x, y, color=palette.get(order, "#111827"), linewidth=1.1,
                          linestyle="--", alpha=.8, label=label if label not in labels else None)
                labels.add(label)
        axis.set_aspect("equal", adjustable="box")
        axis.set_xlabel("Easting (m), EPSG:32617")
        axis.set_ylabel("Northing (m), EPSG:32617")
        axis.set_title("Benchmark independente: D8 derivado do 3DEP × hidrografia 3DHP\n"
                       f"DEM {raster_meta['width']}×{raster_meta['height']}; 3DHP tipo 1={len(river_reference)} linhas no recorte")
        axis.grid(True, alpha=.2)
        axis.legend(loc="upper right", fontsize=7, ncols=2)
        figure.tight_layout()
        figure.savefig(FIGURE, facecolor="white")
        plt.close(figure)

    result = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "scope": "independent public-data benchmark; not ODM project 88 / DTM 72; no application database writes",
        "algorithm": "backend.tools.hydrology: prepare_dem -> priority-flood fill_sinks -> flow_direction D8 -> flow_accumulation -> extract_stream_lines",
        "dem_input": {"path": str(DEM.relative_to(ROOT)), "sha256": digest(DEM),
                      "source_service": "USGS 3DEP Elevation ImageServer", "source_crs": "EPSG:4326",
                      "reference_input": str(REFERENCE.relative_to(ROOT)), "reference_sha256": digest(REFERENCE),
                      "features_returned": len(raw_reference.get("features", [])),
                      "features_in_dem": len(all_reference), "features_in_dem_by_type": dict(sorted(type_counts.items())),
                      "river_type1_features_in_dem": len(river_reference),
                      "river_type1_features_with_order": len(pairable_reference),
                      "river_type1_features_without_order": len(river_reference) - len(pairable_reference),
                      "river_orders_in_dem": sorted({int(p["streamorder"]) for p, _ in pairable_reference})},
        "dem_working_grid": raster_meta,
        "pairing": {"predicted_type": "D8 potential drainage channel (application output)",
                    "reference_type": "USGS 3DHP featuretype=1 River", "key": "Strahler order + line type",
                    "distance_sampling": "predicted line sampled every 1m in EPSG:32617",
                    "tolerances_m": list(TOLERANCES_M)},
        "threshold_sensitivity": results,
        "limitations": [
            "This validates the same algorithm implementation on an independent, coarse 3DEP DEM, not the application ODM DTM #72.",
            "3DEP ImageServer response is resampled to the requested grid; measured working cell size is recorded, and is not fine-resolution lidar validation.",
            "Mapped 3DHP flowlines are not field truth; survey/source dates and hydro-enforcement lineage may differ.",
            "Stream extraction threshold is a parameter; results are reported for all three predeclared thresholds and not selected by best score.",
            "Geometric overlap and distance are similarity measures, not regulatory/engineering acceptance or positional accuracy certification."
        ],
        "artifacts": {"clipped_reference": str(CLIPPED.relative_to(ROOT)),
                      "comparison_map": str(FIGURE.relative_to(ROOT))},
    }
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"features_in_dem": len(all_reference), "type1_lines": len(river_reference),
                      "type1_lines_with_order": len(pairable_reference),
                      "dem_grid": raster_meta,
                      "thresholds": {k: {"predicted_features": v["predicted_features"],
                                         "orders_compared": v["orders_compared"],
                                         "order_coverage_50m": {o: round(m["tolerances"]["50"]["coverage_predicted_pct"], 2)
                                                                 for o, m in v["by_order"].items()}}
                                     for k, v in results.items()},
                      "result": str(RESULT), "map": str(FIGURE)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
