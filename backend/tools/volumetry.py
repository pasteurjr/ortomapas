"""Volume calculation tools for DSM analysis."""
import numpy as np
import rasterio
import logging

logger = logging.getLogger(__name__)

def calc_volume(dsm_path: str, reference_elevation: float, output_path: str = None) -> dict:
    """Calculate volume above and below a reference elevation plane."""
    with rasterio.open(dsm_path) as src:
        from backend.utils.raster_metrics import volume_metrics
        dsm = src.read(1, masked=True).astype(float)
        metrics = volume_metrics(dsm, src.crs, src.transform, reference_elevation)
        nodata = src.nodata

        if nodata is not None:
            mask = (np.asarray(dsm) != nodata) & np.isfinite(np.asarray(dsm)) & ~np.ma.getmaskarray(dsm)
        else:
            mask = np.isfinite(np.asarray(dsm)) & ~np.ma.getmaskarray(dsm)

        pixel_area_m2 = metrics['pixel_area_m2']

        diff = dsm - reference_elevation
        diff_masked = np.where(mask, diff, 0)

        volume_above = metrics['volume_above_m3']
        volume_below = metrics['volume_below_m3']

        if output_path:
            profile = src.profile.copy()
            profile.update(dtype='float32', count=1, nodata=-9999)
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(np.where(mask, diff_masked, -9999).astype('float32'), 1)

        return {
            "volume_above_m3": round(volume_above, 2),
            "volume_below_m3": round(volume_below, 2),
            "net_volume_m3": round(volume_above - volume_below, 2),
            "reference_elevation_m": reference_elevation,
            "pixel_area_m2": round(pixel_area_m2, 4),
            "output_path": output_path,
            "vertical_units": "m", "vertical_units_assumed": True
        }

def dsm_difference(dsm1_path: str, dsm2_path: str, output_path: str) -> dict:
    """Calculate difference between two DSMs (dsm2 - dsm1)."""
    with rasterio.open(dsm1_path) as src1:
        dsm1 = src1.read(1).astype(float)
        profile = src1.profile.copy()
        transform = src1.transform
        crs = src1.crs
        nodata1 = src1.nodata

    with rasterio.open(dsm2_path) as src2:
        dsm2 = src2.read(1).astype(float)
        nodata2 = src2.nodata

    mask = np.ones_like(dsm1, dtype=bool)
    if nodata1 is not None:
        mask &= dsm1 != nodata1
    if nodata2 is not None:
        mask &= dsm2 != nodata2

    diff = np.where(mask, dsm2 - dsm1, -9999)

    profile.update(dtype='float32', count=1, nodata=-9999)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(diff.astype('float32'), 1)

    valid_diff = diff[mask]

    # Calculate pixel area
    pixel_width = abs(transform[0])
    pixel_height = abs(transform[4])
    if crs and crs.is_geographic:
        center_lat = (rasterio.open(dsm1_path).bounds.top + rasterio.open(dsm1_path).bounds.bottom) / 2
        meter_per_deg_lon = 111320 * np.cos(np.radians(center_lat))
        meter_per_deg_lat = 110540
        pixel_area_m2 = (pixel_width * meter_per_deg_lon) * (pixel_height * meter_per_deg_lat)
    else:
        pixel_area_m2 = pixel_width * pixel_height

    return {
        "output_path": output_path,
        "min_diff_m": float(np.min(valid_diff)) if len(valid_diff) > 0 else 0,
        "max_diff_m": float(np.max(valid_diff)) if len(valid_diff) > 0 else 0,
        "mean_diff_m": float(np.mean(valid_diff)) if len(valid_diff) > 0 else 0,
        "std_diff_m": float(np.std(valid_diff)) if len(valid_diff) > 0 else 0,
    }

def cut_fill_analysis(dsm_before_path: str, dsm_after_path: str, output_path: str) -> dict:
    """Classify changes as cut (negative) or fill (positive)."""
    result = dsm_difference(dsm_before_path, dsm_after_path, output_path)

    with rasterio.open(output_path) as src:
        diff = src.read(1)
        nodata = src.nodata
        transform = src.transform
        crs = src.crs

        mask = diff != nodata if nodata else np.isfinite(diff)

        pixel_width = abs(transform[0])
        pixel_height = abs(transform[4])
        if crs and crs.is_geographic:
            center_lat = (src.bounds.top + src.bounds.bottom) / 2
            meter_per_deg_lon = 111320 * np.cos(np.radians(center_lat))
            meter_per_deg_lat = 110540
            pixel_area_m2 = (pixel_width * meter_per_deg_lon) * (pixel_height * meter_per_deg_lat)
        else:
            pixel_area_m2 = pixel_width * pixel_height

        cut_mask = mask & (diff < -0.1)
        fill_mask = mask & (diff > 0.1)

        cut_volume = float(np.sum(np.abs(diff[cut_mask])) * pixel_area_m2)
        fill_volume = float(np.sum(diff[fill_mask]) * pixel_area_m2)
        cut_area = float(np.sum(cut_mask) * pixel_area_m2)
        fill_area = float(np.sum(fill_mask) * pixel_area_m2)

    result.update({
        "cut_volume_m3": round(cut_volume, 2),
        "fill_volume_m3": round(fill_volume, 2),
        "cut_area_m2": round(cut_area, 2),
        "fill_area_m2": round(fill_area, 2),
        "net_volume_m3": round(fill_volume - cut_volume, 2)
    })
    return result
