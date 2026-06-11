"""
GDAL operations via subprocess for the orthomapping system.

Every function runs a GDAL CLI tool as a subprocess, checks the return code,
raises RuntimeError on failure, and returns the output_path on success.
"""

import json
import logging
import os
import subprocess
import tempfile
from typing import Optional

logger = logging.getLogger(__name__)


def _run(cmd: list[str], description: str = "") -> subprocess.CompletedProcess:
    """Run a subprocess command and raise on non-zero exit."""
    logger.info("Running %s: %s", description or cmd[0], " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if result.returncode != 0:
        msg = (
            f"GDAL command failed ({description}): "
            f"returncode={result.returncode}\n"
            f"stderr: {result.stderr}\n"
            f"stdout: {result.stdout}"
        )
        logger.error(msg)
        raise RuntimeError(msg)
    logger.info("%s completed successfully.", description or cmd[0])
    return result


def clip_raster(
    input_path: str,
    output_path: str,
    bbox: Optional[list[float]] = None,
    polygon_wkt: Optional[str] = None,
) -> str:
    """
    Clip a raster using gdalwarp.

    Parameters
    ----------
    input_path : str
        Path to input raster.
    output_path : str
        Path for clipped output raster.
    bbox : list[float], optional
        Bounding box as [xmin, ymin, xmax, ymax].
    polygon_wkt : str, optional
        WKT geometry to use as cutline.

    Returns
    -------
    str
        output_path on success.
    """
    if bbox is None and polygon_wkt is None:
        raise ValueError("Either bbox or polygon_wkt must be provided.")

    cmd = ["gdalwarp", "-overwrite"]

    if bbox is not None:
        xmin, ymin, xmax, ymax = bbox
        cmd += ["-te", str(xmin), str(ymin), str(xmax), str(ymax)]

    if polygon_wkt is not None:
        # Write WKT to a temporary GeoJSON file for use as cutline
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": _wkt_to_geojson_geometry(polygon_wkt),
                    "properties": {},
                }
            ],
        }
        cutline_fd, cutline_path = tempfile.mkstemp(suffix=".geojson")
        try:
            with os.fdopen(cutline_fd, "w") as f:
                json.dump(geojson, f)
            cmd += ["-cutline", cutline_path, "-crop_to_cutline"]
            cmd += [input_path, output_path]
            _run(cmd, "clip_raster")
        finally:
            if os.path.exists(cutline_path):
                os.remove(cutline_path)
        return output_path

    cmd += [input_path, output_path]
    _run(cmd, "clip_raster")
    return output_path


def _wkt_to_geojson_geometry(wkt: str) -> dict:
    """
    Minimal WKT to GeoJSON geometry conversion using ogr2ogr via osgeo,
    falling back to a simple parser for POLYGON WKT.
    """
    wkt = wkt.strip()
    upper = wkt.upper()

    if upper.startswith("POLYGON"):
        # Parse POLYGON ((x1 y1, x2 y2, ...))
        inner = wkt[wkt.index("(") :]
        # Remove outer parens for POLYGON
        inner = inner.strip()
        if inner.startswith("(("):
            inner = inner[2:]
        if inner.endswith("))"):
            inner = inner[:-2]
        rings = inner.split("),(")
        coordinates = []
        for ring in rings:
            ring = ring.strip("() ")
            coords = []
            for pair in ring.split(","):
                parts = pair.strip().split()
                coords.append([float(parts[0]), float(parts[1])])
            coordinates.append(coords)
        return {"type": "Polygon", "coordinates": coordinates}

    if upper.startswith("MULTIPOLYGON"):
        inner = wkt[wkt.index("(") :]
        inner = inner.strip()
        if inner.startswith("((("):
            inner = inner[3:-3]
        polygons_str = inner.split(")),((")
        coordinates = []
        for poly_str in polygons_str:
            rings = poly_str.split("),(")
            poly_coords = []
            for ring in rings:
                ring = ring.strip("() ")
                coords = []
                for pair in ring.split(","):
                    parts = pair.strip().split()
                    coords.append([float(parts[0]), float(parts[1])])
                poly_coords.append(coords)
            coordinates.append(poly_coords)
        return {"type": "MultiPolygon", "coordinates": coordinates}

    # Fallback: pass raw WKT — this might fail for complex geometries
    raise ValueError(f"Unsupported WKT type for conversion: {wkt[:40]}...")


def reproject_raster(input_path: str, output_path: str, target_epsg: int) -> str:
    """Reproject raster to target EPSG using gdalwarp."""
    cmd = [
        "gdalwarp",
        "-overwrite",
        "-t_srs",
        f"EPSG:{target_epsg}",
        input_path,
        output_path,
    ]
    _run(cmd, "reproject_raster")
    return output_path


def merge_rasters(input_paths: list[str], output_path: str) -> str:
    """Merge multiple rasters using gdal_merge.py."""
    if not input_paths:
        raise ValueError("input_paths must contain at least one path.")
    cmd = ["gdal_merge.py", "-o", output_path, "-co", "COMPRESS=LZW"] + input_paths
    _run(cmd, "merge_rasters")
    return output_path


def translate_raster(
    input_path: str,
    output_path: str,
    format: str = "GTiff",
    options: Optional[list[str]] = None,
) -> str:
    """Translate / convert a raster using gdal_translate."""
    cmd = ["gdal_translate", "-of", format]
    if options:
        cmd += options
    cmd += [input_path, output_path]
    _run(cmd, "translate_raster")
    return output_path


def raster_info(input_path: str) -> dict:
    """Run gdalinfo -json and return parsed dict."""
    cmd = ["gdalinfo", "-json", input_path]
    result = _run(cmd, "raster_info")
    return json.loads(result.stdout)


def generate_contours(
    input_path: str,
    output_path: str,
    interval: float = 5.0,
    attribute_name: str = "elevation",
) -> str:
    """Generate contour lines using gdal_contour, output as GeoJSON."""
    cmd = [
        "gdal_contour",
        "-a",
        attribute_name,
        "-i",
        str(interval),
        "-f",
        "GeoJSON",
        input_path,
        output_path,
    ]
    _run(cmd, "generate_contours")
    return output_path


def hillshade(
    input_path: str,
    output_path: str,
    azimuth: float = 315,
    altitude: float = 45,
) -> str:
    """Generate hillshade raster using gdaldem."""
    cmd = [
        "gdaldem",
        "hillshade",
        input_path,
        output_path,
        "-az",
        str(azimuth),
        "-alt",
        str(altitude),
        "-compute_edges",
    ]
    _run(cmd, "hillshade")
    return output_path


def build_overviews(
    input_path: str,
    levels: Optional[list[int]] = None,
) -> str:
    """Build raster overviews using gdaladdo."""
    if levels is None:
        levels = [2, 4, 8, 16]
    cmd = ["gdaladdo", "-r", "average", input_path] + [str(l) for l in levels]
    _run(cmd, "build_overviews")
    return input_path


def calc_tpi(input_path: str, output_path: str) -> str:
    """Calculate Topographic Position Index using gdaldem TPI."""
    cmd = ["gdaldem", "TPI", input_path, output_path, "-compute_edges"]
    _run(cmd, "calc_tpi")
    return output_path


def calc_tri(input_path: str, output_path: str) -> str:
    """Calculate Terrain Ruggedness Index using gdaldem TRI."""
    cmd = ["gdaldem", "TRI", input_path, output_path, "-compute_edges"]
    _run(cmd, "calc_tri")
    return output_path
