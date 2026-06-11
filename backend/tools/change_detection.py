"""
Change detection tools for multi-temporal raster analysis.

Provides functions to detect spatial changes between two rasters captured
at different dates, compute vegetation change, and produce statistics.
"""

import logging

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform

from backend.tools.raster_analysis import calc_vegetation_index

logger = logging.getLogger(__name__)


def _align_rasters(path1: str, path2: str):
    """
    Read two rasters and align them to the same grid (shape, transform, CRS).

    Uses the first raster as the reference grid. Reprojects/resamples the second
    raster to match.

    Returns
    -------
    tuple
        (data1: ndarray[bands,h,w], data2: ndarray[bands,h,w], profile: dict)
    """
    with rasterio.open(path1) as src1:
        data1 = src1.read().astype(np.float64)
        profile = src1.profile.copy()
        dst_crs = src1.crs
        dst_transform = src1.transform
        dst_width = src1.width
        dst_height = src1.height
        nodata1 = src1.nodata

    with rasterio.open(path2) as src2:
        n_bands = min(data1.shape[0], src2.count)
        data2 = np.empty((n_bands, dst_height, dst_width), dtype=np.float64)

        for band_idx in range(n_bands):
            band_data = src2.read(band_idx + 1).astype(np.float64)
            if (
                src2.crs == dst_crs
                and src2.transform == dst_transform
                and src2.width == dst_width
                and src2.height == dst_height
            ):
                data2[band_idx] = band_data
            else:
                reproject(
                    source=band_data,
                    destination=data2[band_idx],
                    src_transform=src2.transform,
                    src_crs=src2.crs,
                    dst_transform=dst_transform,
                    dst_crs=dst_crs,
                    resampling=Resampling.bilinear,
                )

    # Trim to common band count
    data1 = data1[:n_bands]
    return data1, data2, profile


def detect_changes(
    raster1_path: str,
    raster2_path: str,
    output_path: str,
    threshold: float = 30.0,
) -> str:
    """
    Detect changes between two rasters.

    Aligns the rasters, computes per-band absolute difference, averages
    across bands, and creates a binary change mask where pixels exceeding
    the threshold are marked as changed (value=255, unchanged=0).

    Parameters
    ----------
    raster1_path : str
        Path to the earlier raster.
    raster2_path : str
        Path to the later raster.
    output_path : str
        Destination GeoTIFF for the binary change mask.
    threshold : float
        Pixel value difference threshold to classify as changed.

    Returns
    -------
    str
        output_path on success.
    """
    data1, data2, profile = _align_rasters(raster1_path, raster2_path)

    # Per-band absolute difference, then mean across bands
    diff = np.mean(np.abs(data2 - data1), axis=0)

    # Binary mask
    change_mask = np.where(diff > threshold, 255, 0).astype(np.uint8)

    profile.update(dtype=rasterio.uint8, count=1, compress="lzw", nodata=None)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(change_mask, 1)

    logger.info("Change detection map written to %s", output_path)
    return output_path


def vegetation_change(
    raster1_path: str,
    raster2_path: str,
    output_path: str,
    index: str = "VARI",
) -> str:
    """
    Compute vegetation index change between two dates.

    Calculates the selected vegetation index for both rasters, subtracts
    (date2 - date1), and classifies as:
      - 1 = increase (positive difference > 0.05)
      - 0 = stable (abs difference <= 0.05)
      - -1 = decrease (negative difference < -0.05)

    The output is a single-band GeoTIFF with values -1, 0, 1.

    Parameters
    ----------
    raster1_path : str
        Earlier date raster.
    raster2_path : str
        Later date raster.
    output_path : str
        Destination for classified change raster.
    index : str
        Vegetation index name (VARI, TGI, ExG, GLI).

    Returns
    -------
    str
        output_path on success.
    """
    import tempfile
    import os

    # Compute index for both dates using temporary files
    tmp1_fd, tmp1 = tempfile.mkstemp(suffix="_idx1.tif")
    tmp2_fd, tmp2 = tempfile.mkstemp(suffix="_idx2.tif")
    os.close(tmp1_fd)
    os.close(tmp2_fd)

    try:
        calc_vegetation_index(raster1_path, tmp1, index_name=index)
        calc_vegetation_index(raster2_path, tmp2, index_name=index)

        with rasterio.open(tmp1) as src1:
            idx1 = src1.read(1).astype(np.float64)
            profile = src1.profile.copy()
            nodata = src1.nodata

        with rasterio.open(tmp2) as src2:
            idx2_raw = src2.read(1).astype(np.float64)
            # Align if shapes differ
            if idx2_raw.shape != idx1.shape:
                idx2 = np.empty_like(idx1)
                reproject(
                    source=idx2_raw,
                    destination=idx2,
                    src_transform=src2.transform,
                    src_crs=src2.crs,
                    dst_transform=profile["transform"],
                    dst_crs=profile["crs"],
                    resampling=Resampling.bilinear,
                )
            else:
                idx2 = idx2_raw
    finally:
        for p in (tmp1, tmp2):
            if os.path.exists(p):
                os.remove(p)

    # Replace nodata with NaN
    if nodata is not None:
        idx1[idx1 == nodata] = np.nan
        idx2[idx2 == nodata] = np.nan

    diff = idx2 - idx1
    stability_threshold = 0.05

    classified = np.zeros_like(diff, dtype=np.int16)
    classified[diff > stability_threshold] = 1
    classified[diff < -stability_threshold] = -1
    classified[np.isnan(diff)] = -9999

    profile.update(dtype=rasterio.int16, count=1, compress="lzw", nodata=-9999)

    with rasterio.open(output_path, "w", **profile) as dst:
        dst.write(classified, 1)

    logger.info("Vegetation change map written to %s", output_path)
    return output_path


def change_statistics(change_map_path: str) -> dict:
    """
    Compute statistics from a binary change mask (as produced by detect_changes).

    Parameters
    ----------
    change_map_path : str
        Path to a change mask GeoTIFF (255=changed, 0=unchanged).

    Returns
    -------
    dict
        total_pixels, changed_pixels, unchanged_pixels, percent_changed,
        area_changed_m2, area_changed_ha.
    """
    with rasterio.open(change_map_path) as src:
        data = src.read(1)
        transform = src.transform
        nodata = src.nodata

    # Pixel area in map units (assumed metres)
    pixel_area_m2 = abs(transform.a * transform.e)

    if nodata is not None:
        valid_mask = data != nodata
    else:
        valid_mask = np.ones_like(data, dtype=bool)

    valid_data = data[valid_mask]
    total_pixels = int(valid_data.size)
    changed_pixels = int(np.count_nonzero(valid_data))
    unchanged_pixels = total_pixels - changed_pixels
    percent_changed = (changed_pixels / total_pixels * 100.0) if total_pixels > 0 else 0.0
    area_changed_m2 = changed_pixels * pixel_area_m2
    area_changed_ha = area_changed_m2 / 10000.0

    stats = {
        "total_pixels": total_pixels,
        "changed_pixels": changed_pixels,
        "unchanged_pixels": unchanged_pixels,
        "percent_changed": round(percent_changed, 2),
        "area_changed_m2": round(area_changed_m2, 2),
        "area_changed_ha": round(area_changed_ha, 4),
    }

    logger.info("Change statistics: %s", stats)
    return stats
