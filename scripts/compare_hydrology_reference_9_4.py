"""Compare the queued D8 network with clipped USGS 3DHP flowlines.

Inputs are the real application export and the public 3DHP service response
under docs/validacao/ortomapas_conclusao/etapa-09/. No database writes occur.
"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from pyproj import Transformer
from shapely.geometry import box, mapping, shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/validacao/ortomapas_conclusao/etapa-09"
SOURCE_MANIFEST = EVIDENCE / "uc020_dtm_real.json"
PREDICTED = EVIDENCE / "playwright/04_drenagem_exportada.geojson"
REFERENCE_RAW = EVIDENCE / "referencias/3dhp_flowlines_aukerman.geojson"
REFERENCE_CLIP = EVIDENCE / "referencias/3dhp_flowlines_dtm_clip.geojson"
REFERENCE_METADATA = EVIDENCE / "referencias/3dhp_source_metadata.json"
RESULT = EVIDENCE / "referencias/comparacao_3dhp_d8.json"
FIGURE = EVIDENCE / "referencias/comparacao_rede_d8_3dhp.png"
CRS = "EPSG:32617"
TOLERANCES_M = (2.0, 5.0, 10.0)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_features(path: Path, transformer: Transformer, clip):
    data = json.loads(path.read_text(encoding="utf-8"))
    features = []
    for raw in data.get("features", []):
        geom = transform(transformer.transform, shape(raw["geometry"]))
        if clip is not None:
            geom = geom.intersection(clip)
        if geom.is_empty or geom.length <= 0:
            continue
        features.append((raw.get("properties", {}), geom))
    return features


def geometry_by_class(features, class_key):
    grouped = defaultdict(list)
    for properties, geom in features:
        grouped[int(properties.get(class_key, 0) or 0)].append(geom)
    return {key: unary_union(geoms) for key, geoms in grouped.items()}


def sample_distance(source, target, interval_m=1.0):
    if source.is_empty or target.is_empty or source.length <= 0:
        return None
    count = max(1, int(source.length / interval_m))
    distances = [source.interpolate(min(source.length, index * interval_m)).distance(target)
                 for index in range(count + 1)]
    distances.sort()
    return {
        "sample_interval_m": interval_m,
        "sample_count": len(distances),
        "mean_m": sum(distances) / len(distances),
        "median_m": distances[len(distances) // 2],
        "p95_m": distances[min(len(distances) - 1, int(0.95 * len(distances)))],
        "max_sampled_m": distances[-1],
    }


def coverage(source, target, tolerance_m):
    if source.is_empty or source.length <= 0 or target.is_empty:
        return {"matched_length_m": 0.0, "total_length_m": float(source.length), "coverage_pct": None}
    matched = float(source.intersection(target.buffer(tolerance_m)).length)
    return {"matched_length_m": matched, "total_length_m": float(source.length),
            "coverage_pct": 100.0 * matched / float(source.length)}


def main():
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    west, south, east, north = manifest["source"]["bounds"]
    bounds = box(west, south, east, north)
    transformer = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
    inverse = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)

    predicted_features = line_features(PREDICTED, transformer, bounds)
    reference_candidates = line_features(REFERENCE_RAW, transformer, None)
    reference_features = [(props, intersection) for props, geom in reference_candidates
                          if not (intersection := geom.intersection(bounds)).is_empty and intersection.length > 0]
    reference_type_counts = defaultdict(int)
    for props, geom in reference_features:
        reference_type_counts[str(props.get("featuretype"))] += 1
    predicted_by_order = geometry_by_class(predicted_features, "ordem_strahler")
    reference_by_order = geometry_by_class(reference_features, "streamorder")

    # Save the actual reference after clipping to the source DTM footprint.
    clipped = []
    for props, geom in reference_features:
        clipped.append({"type": "Feature", "properties": props,
                       "geometry": mapping(transform(inverse.transform, geom))})
    clipped_fc = {"type": "FeatureCollection", "features": clipped}
    REFERENCE_CLIP.write_text(json.dumps(clipped_fc, ensure_ascii=False, separators=(",", ":")) + "\n",
                              encoding="utf-8")

    predicted_orders = sorted(predicted_by_order)
    reference_orders = sorted(reference_by_order)
    orders = sorted(set(predicted_orders) & set(reference_orders))
    by_order = {}
    for order in orders if reference_features else []:
        predicted = predicted_by_order.get(order, box(0, 0, 0, 0).boundary)
        reference = reference_by_order.get(order, box(0, 0, 0, 0).boundary)
        metrics = {
            "feature_type_pair": "Ortomapas D8 potential channel ↔ USGS 3DHP featuretype=1 (River/Channel Line)",
            "strahler_order": order,
            "predicted_length_m": float(predicted.length),
            "reference_length_m": float(reference.length),
            "predicted_feature_count": sum(int(p.get("ordem_strahler", 0)) == order for p, _ in predicted_features),
            "reference_feature_count": sum(int(p.get("streamorder", 0) or 0) == order for p, _ in reference_features),
            "predicted_to_reference_sampled_distance": sample_distance(predicted, reference),
            "reference_to_predicted_sampled_distance": sample_distance(reference, predicted),
            "tolerance_sensitivity": {},
        }
        for tolerance in TOLERANCES_M:
            metrics["tolerance_sensitivity"][f"{tolerance:g}m"] = {
                "predicted_network_coverage": coverage(predicted, reference, tolerance),
                "reference_network_coverage": coverage(reference, predicted, tolerance),
            }
        by_order[str(order)] = metrics

    # Draw the matched DTM footprint and both complete clipped networks.
    figure, axis = plt.subplots(figsize=(12, 8), dpi=160)
    colors = {1: "#2563eb", 2: "#e11d48", 3: "#16a34a", 4: "#7c3aed", 5: "#d97706"}
    x0, y0, x1, y1 = bounds.bounds
    axis.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], color="#222", linewidth=1.2,
              label="Extensão do DTM (fonte comum)")
    for order in sorted(set(predicted_orders) | set(reference_orders)):
        color = colors.get(order, "#111827")
        for props, geom in predicted_features:
            if int(props.get("ordem_strahler", 0)) == order:
                parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
                for part in parts:
                    xx, yy = part.xy
                    axis.plot(xx, yy, color=color, linewidth=1.7, linestyle="-",
                              label=f"D8 ordem {order}" if not axis.get_legend_handles_labels()[1].count(f"D8 ordem {order}") else None)
        for props, geom in reference_features:
            if int(props.get("streamorder", 0) or 0) == order:
                parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
                for part in parts:
                    xx, yy = part.xy
                    axis.plot(xx, yy, color=color, linewidth=1.4, linestyle="--",
                              label=f"USGS 3DHP ordem {order}" if not axis.get_legend_handles_labels()[1].count(f"USGS 3DHP ordem {order}") else None)
    if not reference_features:
        for _, geom in reference_candidates:
            parts = list(geom.geoms) if geom.geom_type == "MultiLineString" else [geom]
            for part in parts:
                xx, yy = part.xy
                axis.plot(xx, yy, color="#dc2626", linewidth=1.4, linestyle="--",
                          label="USGS 3DHP próximo, fora do DTM" if "USGS 3DHP próximo, fora do DTM" not in axis.get_legend_handles_labels()[1] else None)
    axis.set_aspect("equal", adjustable="box")
    axis.set_xlabel("Easting (m), EPSG:32617")
    axis.set_ylabel("Northing (m), EPSG:32617")
    axis.set_title("Rede D8 do Ortomapas × USGS 3DHP — cobertura da área fonte\n" +
                   f"{len(predicted_features)} feições D8; {len(reference_features)} referências no DTM; {len(reference_candidates)} candidatas próximas")
    if not reference_features:
        axis.text(0.01, 0.01, "Nenhuma feição 3DHP intersecta o DTM. Sem pareamento válido por ordem/tipo.",
                  transform=axis.transAxes, color="#b91c1c", fontsize=9, weight="bold",
                  bbox={"facecolor": "white", "alpha": 0.92, "edgecolor": "#b91c1c"})
    axis.grid(True, alpha=0.2)
    axis.legend(loc="upper left", fontsize=8, ncols=2)
    figure.tight_layout()
    figure.savefig(FIGURE, facecolor="white")
    plt.close(figure)

    nearby_reference = unary_union([geom for _, geom in reference_candidates]) if reference_candidates else None
    predicted_all = unary_union([geom for _, geom in predicted_features]) if predicted_features else None
    result = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "source_dtm": {"project_id": manifest["source"]["project_id"],
                       "asset_id": manifest["source"]["asset_id"], "crs": CRS,
                       "bounds_projected_m": [west, south, east, north],
                       "source_grid": [manifest["source"]["width"], manifest["source"]["height"]],
                       "analysis_working_grid_drainage": next(x["working_grid"] for x in manifest["operations"] if x["operation"] == "flow_accumulation")},
        "predicted_input": {"path": str(PREDICTED.relative_to(ROOT)), "sha256": digest(PREDICTED),
                            "features": len(predicted_features), "algorithm": "priority-flood + D8",
                            "parameters": {"minimum_area_m2": 1000, "minimum_strahler_order": 1}},
        "reference_input": {"path": str(REFERENCE_RAW.relative_to(ROOT)), "sha256": digest(REFERENCE_RAW),
                            "metadata_path": str(REFERENCE_METADATA.relative_to(ROOT)),
                            "service_layer": 50, "query_envelope_wgs84": [-81.76, 41.30, -81.748, 41.308],
                            "feature_count_returned": len(reference_candidates),
                            "featuretype_counts_in_query": dict(sorted((str(p.get("featuretype")), sum(str(q.get("featuretype")) == str(p.get("featuretype")) for q, _ in reference_candidates)) for p, _ in reference_candidates)),
                            "features_inside_dtm": len(reference_features), "featuretype_counts_inside_dtm": dict(reference_type_counts),
                            "clip_crs": CRS,
                            "nearest_candidate_to_dtm_edge_m": float(bounds.distance(nearby_reference)) if nearby_reference else None,
                            "nearest_d8_to_candidate_network_m": float(predicted_all.distance(nearby_reference)) if (predicted_all and nearby_reference) else None},
        "comparison_status": "not_comparable_reference_does_not_intersect_dtm" if not reference_features else "metrics_calculated",
        "pairing": {"key": "Strahler order + feature type", "predicted_class": "modeled potential D8 channels (type not stored by result)",
                    "reference_class": "USGS 3DHP featuretype=1 River/Channel Line",
                    "predicted_orders_available": predicted_orders, "reference_orders_inside_dtm": reference_orders,
                    "orders_compared": orders, "valid_pairs": sum(by_order[str(order)]["predicted_feature_count"] > 0 and by_order[str(order)]["reference_feature_count"] > 0 for order in orders)},
        "distance_sampling": "uniform 1 m samples on the metric polylines; reports nearest-network distance, not point positional accuracy",
        "tolerance_sensitivity_m": list(TOLERANCES_M),
        "by_order": by_order,
        "limits": [
            "3DHP is a public reference dataset, not field truth; its 2023 featuredate and acquisition/source lineage may not match the ODM DTM.",
            "The USGS describes 3DHP flowline data as not intended for site-specific regulatory determinations or critical use without awareness of limitations.",
            "The application network is a generalized DTM-derived potential drainage network; the worker grid is coarser than the source DTM.",
            "Network coverage within 2/5/10 m is a spatial similarity measure, not a hydrological accuracy certification.",
        ],
        "artifacts": {"clipped_reference": str(REFERENCE_CLIP.relative_to(ROOT)),
                      "comparison_map": str(FIGURE.relative_to(ROOT))},
    }
    RESULT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"comparison_status": result["comparison_status"], "reference_features_in_dtm": len(reference_features), "reference_features_in_query": len(reference_candidates), "predicted_features": len(predicted_features),
                      "orders": orders, "by_order": {key: {
                          "predicted_length_m": round(val["predicted_length_m"], 2),
                          "reference_length_m": round(val["reference_length_m"], 2),
                          "coverage_5m": {"predicted_pct": round(val["tolerance_sensitivity"]["5m"]["predicted_network_coverage"]["coverage_pct"] or 0, 2),
                                          "reference_pct": round(val["tolerance_sensitivity"]["5m"]["reference_network_coverage"]["coverage_pct"] or 0, 2)},
                      } for key, val in by_order.items()}, "result": str(RESULT), "map": str(FIGURE)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
