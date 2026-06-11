"""
Raster analysis tools using rasterio and numpy.

Provides vegetation indices, terrain analysis, statistics, and a raster calculator.
"""

import json
import logging
from typing import Optional

import numpy as np
import rasterio
from rasterio.transform import from_bounds
from rasterio.mask import mask as rasterio_mask
from rasterio.warp import reproject, Resampling
from scipy.ndimage import uniform_filter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Vegetation indices
# ---------------------------------------------------------------------------

def calc_vegetation_index(
    input_path: str,
    output_path: str,
    index_name: str = "VARI",
) -> str:
    """
    Calculate a visible-band vegetation index from an RGB ortomapa.

    Supported indices
    -----------------
    - VARI : (G - R) / (G + R - B)
    - TGI  : G - 0.39*R - 0.61*B
    - ExG  : 2*G - R - B
    - GLI  : (2*G - R - B) / (2*G + R + B)

    Parameters
    ----------
    input_path : str
        Path to input RGB raster (bands 1=R, 2=G, 3=B).
    output_path : str
        Destination GeoTIFF for the single-band index.
    index_name : str
        One of VARI, TGI, ExG, GLI.

    Returns
    -------
    str
        output_path on success.
    """
    index_name = index_name.upper()
    supported = ("VARI", "TGI", "EXG", "GLI")
    if index_name not in supported:
        raise ValueError(f"Unsupported index '{index_name}'. Choose from {supported}.")

    with rasterio.open(input_path) as src:
        R = src.read(1).astype(np.float64)
        G = src.read(2).astype(np.float64)
        B = src.read(3).astype(np.float64)
        profile = src.profile.copy()

    # Avoid division by zero
    eps = 1e-10

    if index_name == "VARI":
        denominator = G + R - B
        denominator[np.abs(denominator) < eps] = eps
        result = (G - R) / denominator

    elif index_name == "TGI":
        result = G - 0.39 * R - 0.61 * B

    elif index_name == "EXG":
        result = 2.0 * G - R - B

    elif index_name == "GLI":
        denominator = 2.0 * G + R + B
        denominator[np.abs(denominator) < eps] = eps
        result = (2.0 * G - R - B) / denominator

    # Clamp extreme values
    result = np.clip(result, -1e6, 1e6)
    result[~np.isfinite(result)] = 0.0

    profile.update(
        dtype=rasterio.float32,
        count=1,
        compress="lzw",
        nodata=-9999.0,
    )

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(result.astype(np.float32), 1)

    logger.info("Vegetation index %s written to %s", index_name, output_path)
    return output_path


# ---------------------------------------------------------------------------
# Terrain derivatives
# ---------------------------------------------------------------------------

def calc_slope(dsm_path: str, output_path: str) -> str:
    """
    Calculate slope in degrees from a DSM/DTM raster using numpy gradient.
    """
    with rasterio.open(dsm_path) as src:
        dem = src.read(1).astype(np.float64)
        transform = src.transform
        profile = src.profile.copy()
        nodata = src.nodata

    # Cell sizes from the affine transform
    dx = abs(transform.a)
    dy = abs(transform.e)

    # Replace nodata with NaN for gradient computation
    if nodata is not None:
        dem[dem == nodata] = np.nan

    grad_y, grad_x = np.gradient(dem, dy, dx)
    slope_rad = np.arctan(np.sqrt(grad_x ** 2 + grad_y ** 2))
    slope_deg = np.degrees(slope_rad)
    slope_deg[np.isnan(slope_deg)] = -9999.0

    profile.update(dtype=rasterio.float32, count=1, compress="lzw", nodata=-9999.0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(slope_deg.astype(np.float32), 1)

    logger.info("Slope raster written to %s", output_path)
    return output_path


def calc_aspect(dsm_path: str, output_path: str) -> str:
    """
    Calculate aspect in degrees (0=North, 90=East, 180=South, 270=West).
    """
    with rasterio.open(dsm_path) as src:
        dem = src.read(1).astype(np.float64)
        transform = src.transform
        profile = src.profile.copy()
        nodata = src.nodata

    dx = abs(transform.a)
    dy = abs(transform.e)

    if nodata is not None:
        dem[dem == nodata] = np.nan

    grad_y, grad_x = np.gradient(dem, dy, dx)

    # arctan2 gives angle from east counterclockwise; convert to compass bearing
    aspect_rad = np.arctan2(-grad_y, grad_x)
    aspect_deg = np.degrees(aspect_rad)
    # Convert from math angle to compass: compass = 90 - math_angle
    aspect_compass = 90.0 - aspect_deg
    # Normalize to 0-360
    aspect_compass = aspect_compass % 360.0
    aspect_compass[np.isnan(aspect_compass)] = -9999.0

    profile.update(dtype=rasterio.float32, count=1, compress="lzw", nodata=-9999.0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(aspect_compass.astype(np.float32), 1)

    logger.info("Aspect raster written to %s", output_path)
    return output_path


def calc_roughness(dsm_path: str, output_path: str) -> str:
    """
    Calculate surface roughness as the standard deviation in a 3x3 window.
    """
    with rasterio.open(dsm_path) as src:
        dem = src.read(1).astype(np.float64)
        profile = src.profile.copy()
        nodata = src.nodata

    if nodata is not None:
        dem[dem == nodata] = np.nan

    # Compute local mean and local mean of squares, then std = sqrt(E[x^2] - E[x]^2)
    mean_local = uniform_filter(np.nan_to_num(dem, nan=0.0), size=3, mode="reflect")
    mean_sq = uniform_filter(np.nan_to_num(dem ** 2, nan=0.0), size=3, mode="reflect")
    variance = mean_sq - mean_local ** 2
    variance[variance < 0] = 0.0
    roughness = np.sqrt(variance)

    # Restore nodata
    if nodata is not None:
        roughness[np.isnan(dem)] = -9999.0

    profile.update(dtype=rasterio.float32, count=1, compress="lzw", nodata=-9999.0)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(roughness.astype(np.float32), 1)

    logger.info("Roughness raster written to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def raster_statistics(input_path: str) -> dict:
    """
    Compute per-band statistics: min, max, mean, std, median, histogram.
    """
    with rasterio.open(input_path) as src:
        stats = {}
        for band_idx in range(1, src.count + 1):
            data = src.read(band_idx).astype(np.float64)
            nodata = src.nodata
            # Sempre filtrar NaN/inf para evitar erro no histogram
            finite_mask = np.isfinite(data)
            if nodata is not None:
                valid = data[finite_mask & (data != nodata)]
            else:
                valid = data[finite_mask]

            if valid.size == 0:
                stats[f"band_{band_idx}"] = {
                    "min": None,
                    "max": None,
                    "mean": None,
                    "std": None,
                    "median": None,
                    "histogram": None,
                    "valid_pixels": 0,
                    "total_pixels": int(data.size),
                }
                continue

            hist_values, hist_edges = np.histogram(valid, bins=256)
            stats[f"band_{band_idx}"] = {
                "min": float(np.min(valid)),
                "max": float(np.max(valid)),
                "mean": float(np.mean(valid)),
                "std": float(np.std(valid)),
                "median": float(np.median(valid)),
                "histogram": {
                    "counts": hist_values.tolist(),
                    "edges": hist_edges.tolist(),
                },
                "valid_pixels": int(valid.size),
                "total_pixels": int(data.size),
            }

    logger.info("Statistics computed for %s (%d bands)", input_path, len(stats))
    return stats


# ---------------------------------------------------------------------------
# Zonal statistics
# ---------------------------------------------------------------------------

def zonal_statistics(raster_path: str, zones_geojson_path: str) -> list[dict]:
    """
    Compute per-zone statistics from a raster using zone geometries in a GeoJSON file.

    Returns a list of dicts, one per feature in the GeoJSON, with zone stats.
    """
    with open(zones_geojson_path, "r") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    results = []

    with rasterio.open(raster_path) as src:
        nodata = src.nodata

        for i, feature in enumerate(features):
            geometry = feature.get("geometry")
            properties = feature.get("properties", {})
            zone_name = properties.get("name", properties.get("id", f"zone_{i}"))

            try:
                out_image, out_transform = rasterio_mask(
                    src, [geometry], crop=True, nodata=-9999.0
                )
            except Exception as exc:
                logger.warning("Could not mask zone %s: %s", zone_name, exc)
                results.append({
                    "zone": zone_name,
                    "properties": properties,
                    "error": str(exc),
                })
                continue

            band_stats = {}
            for band_idx in range(out_image.shape[0]):
                band_data = out_image[band_idx].astype(np.float64)
                valid = band_data[band_data != -9999.0]
                if nodata is not None:
                    valid = valid[valid != nodata]
                valid = valid[np.isfinite(valid)]

                if valid.size == 0:
                    band_stats[f"band_{band_idx + 1}"] = {
                        "min": None, "max": None, "mean": None,
                        "std": None, "count": 0,
                    }
                else:
                    band_stats[f"band_{band_idx + 1}"] = {
                        "min": float(np.min(valid)),
                        "max": float(np.max(valid)),
                        "mean": float(np.mean(valid)),
                        "std": float(np.std(valid)),
                        "sum": float(np.sum(valid)),
                        "count": int(valid.size),
                    }

            results.append({
                "zone": zone_name,
                "properties": properties,
                "statistics": band_stats,
            })

    logger.info("Zonal statistics computed for %d zones", len(results))
    return results


# ---------------------------------------------------------------------------
# Raster calculator
# ---------------------------------------------------------------------------

def raster_calculator(
    expression: str,
    input_paths: dict[str, str],
    output_path: str,
) -> str:
    """
    Evaluate a raster expression with named band variables.

    Parameters
    ----------
    expression : str
        Numpy expression using variable names matching keys in input_paths.
        Example: "(B2 - B1) / (B2 + B1)"
    input_paths : dict
        Mapping of variable name to raster file path.
        Example: {"B1": "red.tif", "B2": "green.tif"}
    output_path : str
        Destination GeoTIFF.

    Returns
    -------
    str
        output_path on success.
    """
    if not input_paths:
        raise ValueError("input_paths must contain at least one entry.")

    # Validate expression does not contain dangerous constructs
    forbidden = ["import", "exec", "eval", "__", "open", "os.", "sys.", "subprocess"]
    for word in forbidden:
        if word in expression:
            raise ValueError(f"Expression contains forbidden term: '{word}'")

    # Read all inputs
    bands = {}
    reference_profile = None
    reference_shape = None

    for var_name, path in input_paths.items():
        with rasterio.open(path) as src:
            data = src.read(1).astype(np.float64)
            if reference_profile is None:
                reference_profile = src.profile.copy()
                reference_shape = data.shape
            bands[var_name] = data

    # Verify all shapes match
    for var_name, data in bands.items():
        if data.shape != reference_shape:
            raise ValueError(
                f"Shape mismatch: {var_name} has shape {data.shape}, "
                f"expected {reference_shape}."
            )

    # Build safe namespace
    safe_ns = {"np": np, "numpy": np}
    safe_ns.update(bands)

    # Evaluate
    result = eval(expression, {"__builtins__": {}}, safe_ns)  # noqa: S307
    result = np.asarray(result, dtype=np.float64)
    result[~np.isfinite(result)] = -9999.0

    reference_profile.update(
        dtype=rasterio.float32,
        count=1,
        compress="lzw",
        nodata=-9999.0,
    )

    with rasterio.open(output_path, "w", **reference_profile) as dst:
        dst.write(result.astype(np.float32), 1)

    logger.info("Raster calculator result written to %s", output_path)
    return output_path
