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
    """Align the after raster to the full before grid; calculate after - before."""
    from rasterio.warp import reproject, Resampling
    from backend.utils.raster_metrics import metric_jacobian
    with rasterio.open(dsm1_path) as src1:
        dsm1 = src1.read(1, masked=True).astype(float).filled(np.nan)
        profile = src1.profile.copy()
        transform = src1.transform
        crs = src1.crs
        pixel_area = abs(float(np.linalg.det(metric_jacobian(crs, transform))))
        with rasterio.open(dsm2_path) as src2:
            if not src2.crs:
                raise ValueError('Raster posterior sem CRS')
            dsm2 = np.full(dsm1.shape, np.nan)
            reproject(src2.read(1, masked=True).astype(float).filled(np.nan), dsm2,
                      src_transform=src2.transform, src_crs=src2.crs, src_nodata=np.nan,
                      dst_transform=transform, dst_crs=crs, dst_nodata=np.nan,
                      resampling=Resampling.bilinear)
    mask = np.isfinite(dsm1) & np.isfinite(dsm2)
    if not mask.any():
        raise ValueError('Superficies sem area comum valida')
    diff = np.where(mask, dsm2 - dsm1, -9999)

    profile.update(dtype='float32', count=1, nodata=-9999)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(diff.astype('float32'), 1)
        dst.update_tags(operation='after - before', vertical_units_assumed='m', alignment='after to before grid')

    valid_diff = diff[mask]

    return {
        "output_path": output_path,
        "min_diff_m": float(np.min(valid_diff)) if len(valid_diff) > 0 else 0,
        "max_diff_m": float(np.max(valid_diff)) if len(valid_diff) > 0 else 0,
        "mean_diff_m": float(np.mean(valid_diff)) if len(valid_diff) > 0 else 0,
        "std_diff_m": float(np.std(valid_diff)) if len(valid_diff) > 0 else 0,
        "pixel_area_m2": pixel_area, "valid_pixels": int(mask.sum()),
        "alignment": "after reprojected to before grid", "difference": "after - before",
        "vertical_units_assumed": "m",
    }

def cut_fill_analysis(dsm_before_path: str, dsm_after_path: str, output_path: str) -> dict:
    """Classify changes as cut (negative) or fill (positive)."""
    result = dsm_difference(dsm_before_path, dsm_after_path, output_path)

    with rasterio.open(output_path) as src:
        diff = src.read(1, masked=True).astype(float).filled(np.nan)
        mask = np.isfinite(diff)
        pixel_area_m2 = result['pixel_area_m2']

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
        "net_volume_m3": round(fill_volume - cut_volume, 2),
        "change_threshold_m": 0.1,
    })
    return result
