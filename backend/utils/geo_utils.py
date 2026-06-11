"""
Geospatial utility functions for raster metadata extraction,
coordinate conversions, and geometry transformations.
"""

import json
import logging
from typing import Any, Dict, Optional, Tuple

import numpy as np
import rasterio
from rasterio.transform import xy
from shapely import wkt as shapely_wkt
from shapely.geometry import mapping, shape
from shapely.ops import transform
import pyproj

logger = logging.getLogger(__name__)


def get_raster_info(filepath: str) -> Dict[str, Any]:
    """
    Extract comprehensive metadata from a raster file.

    Returns dict with bbox, resolution, size, crs, bands.
    """
    try:
        with rasterio.open(filepath) as dataset:
            bounds = dataset.bounds
            transform_mat = dataset.transform
            res_x = abs(transform_mat.a)
            res_y = abs(transform_mat.e)

            return {
                "bbox": {
                    "north": bounds.top,
                    "south": bounds.bottom,
                    "east": bounds.right,
                    "west": bounds.left,
                },
                "resolution": {
                    "x": res_x,
                    "y": res_y,
                },
                "size": {
                    "width": dataset.width,
                    "height": dataset.height,
                },
                "crs": str(dataset.crs) if dataset.crs else None,
                "bands": dataset.count,
                "dtype": str(dataset.dtypes[0]),
                "nodata": dataset.nodata,
            }
    except Exception as e:
        logger.error(f"Error reading raster info from {filepath}: {e}")
        raise


def get_raster_bounds(filepath: str) -> Tuple[float, float, float, float]:
    """
    Get raster bounds as (north, south, east, west).
    If the CRS is not EPSG:4326, bounds are reprojected to WGS84.
    """
    try:
        with rasterio.open(filepath) as dataset:
            bounds = dataset.bounds
            if dataset.crs and str(dataset.crs) != "EPSG:4326":
                transformer = pyproj.Transformer.from_crs(
                    dataset.crs, "EPSG:4326", always_xy=True
                )
                west, south = transformer.transform(bounds.left, bounds.bottom)
                east, north = transformer.transform(bounds.right, bounds.top)
                return (north, south, east, west)
            return (bounds.top, bounds.bottom, bounds.right, bounds.left)
    except Exception as e:
        logger.error(f"Error reading raster bounds from {filepath}: {e}")
        raise


def wkt_to_geojson(wkt_string: str) -> Dict[str, Any]:
    """Convert a WKT geometry string to a GeoJSON geometry dict."""
    try:
        geom = shapely_wkt.loads(wkt_string)
        return mapping(geom)
    except Exception as e:
        logger.error(f"Error converting WKT to GeoJSON: {e}")
        raise


def geojson_to_wkt(geojson_geometry: Dict[str, Any]) -> str:
    """Convert a GeoJSON geometry dict to a WKT string."""
    try:
        geom = shape(geojson_geometry)
        return geom.wkt
    except Exception as e:
        logger.error(f"Error converting GeoJSON to WKT: {e}")
        raise


def calc_area_from_wkt(wkt_string: str, source_crs: str = "EPSG:4326") -> float:
    """
    Calculate area in square meters from a WKT geometry string.
    Uses an equal-area projection for accurate measurement.
    """
    try:
        geom = shapely_wkt.loads(wkt_string)

        # Project to an equal-area CRS for accurate area calculation
        project = pyproj.Transformer.from_crs(
            source_crs, "EPSG:6933", always_xy=True
        ).transform
        projected_geom = transform(project, geom)
        return projected_geom.area
    except Exception as e:
        logger.error(f"Error calculating area from WKT: {e}")
        raise


def pixel_to_coords(filepath: str, row: int, col: int) -> Tuple[float, float]:
    """
    Convert pixel coordinates (row, col) to geographic coordinates (lon, lat).
    If the raster CRS is not EPSG:4326, coordinates are reprojected.
    """
    try:
        with rasterio.open(filepath) as dataset:
            x, y = xy(dataset.transform, row, col)

            if dataset.crs and str(dataset.crs) != "EPSG:4326":
                transformer = pyproj.Transformer.from_crs(
                    dataset.crs, "EPSG:4326", always_xy=True
                )
                lon, lat = transformer.transform(x, y)
                return (lat, lon)
            return (y, x)
    except Exception as e:
        logger.error(f"Error converting pixel to coords: {e}")
        raise
