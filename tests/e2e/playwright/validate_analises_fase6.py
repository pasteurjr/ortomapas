"""Independent, read-only audit of real analysis products for Phase 6.

The only new computation is a VARI verification written to a temporary file.
Database products are inspected, never modified. Existing published outputs are
checked against their real source rasters and independent numeric references.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import fiona
import numpy as np
import rasterio
from rasterio.mask import mask as raster_mask
from rasterio.warp import transform_geom

from backend.database.connection import get_connection
from backend.tools.raster_analysis import calc_vegetation_index
from backend.utils.raster_metrics import metric_jacobian

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs/validacao/ortomapas_conclusao/etapa-06"


def db_snapshot() -> tuple[dict, dict]:
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM analises WHERE id = ANY(%s)", ([63, 81, 116, 117, 120, 130, 131, 132, 133, 143],))
        analyses = {row["id"]: dict(row) for row in cur.fetchall()}
        cur.execute("SELECT id, projeto_id, nome, tipo, caminho_arquivo, sistema_coordenadas, largura_px, altura_px FROM ortomapas WHERE id = ANY(%s)", ([30, 34, 35, 36, 46, 47, 48],))
        sources = {row["id"]: dict(row) for row in cur.fetchall()}
    return analyses, sources


def source_path(row: dict) -> Path:
    raw = Path(row["caminho_arquivo"])
    return raw if raw.is_absolute() else ROOT / "data" / raw


def output_path(row: dict) -> Path:
    return Path(row["resultado_path"])


def sample_slope(analysis: dict, source: dict, n: int = 240) -> dict:
    src_path, out_path = source_path(source), output_path(analysis)
    with rasterio.open(src_path) as src, rasterio.open(out_path) as out:
        if (src.crs != out.crs or src.transform != out.transform or
                src.width != out.width or src.height != out.height):
            raise AssertionError(f"A derivada {analysis['id']} não preserva a grade fonte")
        jacobian_inverse = np.linalg.inv(metric_jacobian(src.crs, src.transform).T)
        rng = np.random.default_rng(20261110 + analysis["id"])
        rows = rng.integers(2, src.height - 2, size=n)
        cols = rng.integers(2, src.width - 2, size=n)
        abs_errors = []
        for row, col in zip(rows, cols):
            z = src.read(1, window=((row - 1, row + 2), (col - 1, col + 2))).astype(float)
            result = float(out.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
            if not np.isfinite(z).all() or not np.isfinite(result) or result < 0:
                continue
            dz_dcol = (z[1, 2] - z[1, 0]) / 2
            dz_drow = (z[2, 1] - z[0, 1]) / 2
            east, north = jacobian_inverse @ np.array([dz_dcol, dz_drow])
            expected = np.degrees(np.arctan(np.hypot(east, north)))
            abs_errors.append(abs(expected - result))
        if len(abs_errors) < n * 0.7:
            raise AssertionError(f"Poucas amostras válidas na declividade {analysis['id']}")
        max_error = float(max(abs_errors))
        if max_error > 1e-3:
            raise AssertionError(f"Declividade {analysis['id']}: erro máximo {max_error}°")
        return {"analysis_id": analysis["id"], "source_id": source["id"],
                "crs": src.crs.to_string(), "units": "graus de inclinação",
                "valid_samples": len(abs_errors), "max_abs_error_deg": max_error,
                "samples": n, "grid_preserved": True}


def audit_vari(source: dict) -> dict:
    path = source_path(source)
    with tempfile.TemporaryDirectory(prefix="ortomapas-fase6-vari-") as tmp:
        output = Path(tmp) / "vari.tif"
        calc_vegetation_index(str(path), str(output), "VARI")
        with rasterio.open(path) as src, rasterio.open(output) as dst:
            if src.count < 3 or dst.count != 1:
                raise AssertionError("VARI exige RGB e deve produzir uma banda")
            if src.crs != dst.crs or src.transform != dst.transform:
                raise AssertionError("VARI não preservou georreferenciamento")
            rng = np.random.default_rng(20261110)
            rows = rng.integers(0, src.height, size=400)
            cols = rng.integers(0, src.width, size=400)
            errors = []
            for row, col in zip(rows, cols):
                rgb = src.read([1, 2, 3], window=((row, row + 1), (col, col + 1)), masked=True)
                if np.ma.getmaskarray(rgb).any():
                    continue
                red, green, blue = [float(b[0, 0]) for b in rgb]
                denominator = green + red - blue
                if abs(denominator) < 1e-10:
                    denominator = 1e-10
                expected = (green - red) / denominator
                actual = float(dst.read(1, window=((row, row + 1), (col, col + 1)))[0, 0])
                errors.append(abs(actual - expected))
            if len(errors) < 250 or max(errors) > 2e-6:
                raise AssertionError("VARI divergiu da fórmula independente")
            profile = {"width": dst.width, "height": dst.height,
                       "crs": dst.crs.to_string(), "bands": dst.count,
                       "units": "índice RGB adimensional"}
        invalid_path = Path(tmp) / "ndvi.tif"
        rejected_ndvi = False
        try:
            calc_vegetation_index(str(path), str(invalid_path), "NDVI")
        except ValueError:
            rejected_ndvi = not invalid_path.exists()
        if not rejected_ndvi:
            raise AssertionError("NDVI foi aceito sem banda NIR")
    return {"source_id": source["id"], **profile, "valid_formula_samples": len(errors),
            "max_abs_error": float(max(errors)), "ndvi_without_nir_rejected": True,
            "output_temporary_only": True}


def audit_volume(analysis: dict, source: dict) -> dict:
    params = analysis["parametros"]
    geometry = transform_geom("EPSG:4326", "EPSG:32617", params["aoi"])
    src_path, result_path = source_path(source), output_path(analysis)
    with rasterio.open(src_path) as src, rasterio.open(result_path) as out:
        values, transform = raster_mask(src, [geometry], crop=True, filled=False, indexes=1,
                                        all_touched=False)
        actual = out.read(1, masked=True)
        if actual.shape != values.shape or out.transform != transform:
            raise AssertionError("Volume raster não corresponde à AOI aplicada à fonte")
        valid = ~np.ma.getmaskarray(values) & np.isfinite(np.asarray(values))
        reference = float(params["reference_elevation"])
        diff = np.asarray(values, dtype=np.float64) - reference
        diff[~valid] = 0
        expected = np.ma.asarray(actual).filled(np.nan).astype(np.float64)
        compare = valid & np.isfinite(expected)
        max_px_error = float(np.max(np.abs(expected[compare] - diff[compare])))
        pixel_area = abs(float(transform.a * transform.e - transform.b * transform.d))
        above = float(np.maximum(diff[valid], 0).sum() * pixel_area)
        below = float(np.maximum(-diff[valid], 0).sum() * pixel_area)
        saved = analysis["resultado_json"]["stats"]
        if max_px_error > 1e-5 or abs(above - saved["volume_above_m3"]) > 0.02 or abs(below - saved["volume_below_m3"]) > 0.02:
            raise AssertionError("Volume persistido não confere com a soma independente em float64")
        return {"analysis_id": analysis["id"], "source_id": source["id"],
                "crs": src.crs.to_string(), "pixel_area_m2": pixel_area,
                "reference_elevation_m": reference, "valid_pixels": int(valid.sum()),
                "volume_above_m3": above, "volume_below_m3": below,
                "max_abs_pixel_error_m": max_px_error, "output_matches_source_minus_plane": True}


def audit_outputs(analyses: dict, sources: dict) -> dict:
    rows = {}
    for aid, row in analyses.items():
        path = output_path(row)
        if row["status"] != "concluida" or not path.is_file():
            raise AssertionError(f"Análise {aid} sem status concluído ou arquivo")
        rows[str(aid)] = {"status": row["status"], "type": row["tipo_analise"],
                          "source_id": row["ortomapa_id"], "output": str(path.relative_to(ROOT)),
                          "output_bytes": path.stat().st_size}

    slope = {str(aid): sample_slope(analyses[aid], sources[analyses[aid]["ortomapa_id"]])
             for aid in (116, 117)}

    classification = analyses[120]
    class_path = output_path(classification)
    with rasterio.open(class_path) as ds:
        values = ds.read(1, masked=True)
        unique, counts = np.unique(values.compressed(), return_counts=True)
        if len(unique) != 5 or not np.isin(unique, [1, 2, 3, 4, 5]).all():
            raise AssertionError(f"Classificação #120 esperava rótulos 1..5; obteve {unique}")
        kmeans = {"analysis_id": 120, "source_id": 30, "crs": ds.crs.to_string(),
                  "labels": [int(x) for x in unique], "pixel_counts": [int(x) for x in counts],
                  "valid_pixels": int(counts.sum()), "semantic_class_accuracy": "not assessed; no field labels"}

    volume = audit_volume(analyses[63], sources[34])

    contours = analyses[133]
    with fiona.open(output_path(contours)) as layer:
        feature_count = len(layer)
        if feature_count != contours["resultado_json"]["stats"]["feature_count"]:
            raise AssertionError("Contagem de feições de curvas diverge do manifesto persistido")
        elevations = sorted({float(f["properties"]["elevation_m"]) for f in layer})
    if not elevations or any(abs(x / 10 - round(x / 10)) > 1e-8 for x in elevations):
        raise AssertionError("Curvas não seguem a equidistância de 10 m")
    contours_summary = {"analysis_id": 133, "source_id": 35, "crs_output": "EPSG:4326",
                        "features": feature_count, "interval_m": 10,
                        "elevation_values_m": elevations}

    # Confirm the watershed mask's stored area from the actual raster cells.
    basin = analyses[143]
    with rasterio.open(output_path(basin)) as ds:
        mask = ds.read(1)
        pixel_area = abs(float(ds.transform.a * ds.transform.e - ds.transform.b * ds.transform.d))
        basin_pixels = int(np.count_nonzero(mask == 1))
        basin_area = basin_pixels * pixel_area
        saved_area = basin["resultado_json"]["stats"]["area_m2"]
    if abs(basin_area - saved_area) > 0.02:
        raise AssertionError("Área de bacia não reproduz a contagem independente de células")

    return {"status": "passed", "read_only_database": True,
            "source_dataset": "ODM Aukerman (ortho/DSM/DTM real); sem fotos de Guarajuba",
            "analyses": rows, "vari_real_rgb_recheck": audit_vari(sources[46]),
            "slope_samples": slope, "classification": kmeans, "contours": contours_summary,
            "volume_independent": volume,
            "hydrology_demonstration": {"analysis_id": 143, "source_id": 36,
                "cells": basin_pixels, "pixel_area_m2": pixel_area,
                "recomputed_area_m2": basin_area, "saved_area_m2": saved_area,
                "independent_hydrographic_reference": "not found for this extent; not operationally certified"},
            "change_analysis": {"analysis_id": 81, "before_id": 34, "after_id": 35,
                "controlled_change_fixture": True,
                "interpretation": "validates sign, AOI, pixel alignment and volume math; does not prove temporal change detection on two real dates"}}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    analyses, sources = db_snapshot()
    required_a = {63, 81, 116, 117, 120, 130, 131, 132, 133, 143}
    required_s = {30, 34, 35, 36, 46, 47, 48}
    if required_a - analyses.keys() or required_s - sources.keys():
        raise AssertionError("Faltam análises/fontes reais requeridas no PostgreSQL")
    result = audit_outputs(analyses, sources)
    target = OUT / "manifest.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
