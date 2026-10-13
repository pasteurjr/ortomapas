"""Volume calculation tools for DSM analysis."""
import numpy as np
import rasterio
import logging

logger = logging.getLogger(__name__)

def calc_volume(dsm_path: str, reference_elevation: float, output_path: str = None, aoi=None) -> dict:
    """Calculate volume above and below a reference elevation plane."""
    with rasterio.open(dsm_path) as src:
        from backend.utils.raster_metrics import volume_metrics
        affine = src.transform
        if aoi:
            from rasterio.mask import mask as raster_mask
            values, affine = raster_mask(src, [aoi['projected']], crop=True, all_touched=False, filled=False, indexes=1)
            dsm = values.astype(float)
        else:
            dsm = src.read(1, masked=True).astype(float)
        metrics = volume_metrics(dsm, src.crs, affine, reference_elevation)
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
            profile.update(dtype='float32', count=1, nodata=np.nan, width=dsm.shape[1], height=dsm.shape[0], transform=affine)
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(np.where(mask, diff_masked, np.nan).astype('float32'), 1)
                dst.update_tags(operation='model - reference', reference_elevation_m=reference_elevation,
                                vertical_units_assumed='m', analysis_scope='aoi' if aoi else 'full raster')

        return {
            "volume_above_m3": round(volume_above, 2),
            "volume_below_m3": round(volume_below, 2),
            "net_volume_m3": round(volume_above - volume_below, 2),
            "reference_elevation_m": reference_elevation,
            "pixel_area_m2": pixel_area_m2,
            "valid_pixels": int(mask.sum()),
            "valid_area_m2": float(mask.sum()*pixel_area_m2),
            "cut_area_m2": float(((diff_masked > 0) & mask).sum()*pixel_area_m2),
            "fill_area_m2": float(((diff_masked < 0) & mask).sum()*pixel_area_m2),
            "output_path": output_path,
            "vertical_units": "m", "vertical_units_assumed": True
        }

def dsm_difference(dsm1_path: str, dsm2_path: str, output_path: str, aoi=None) -> dict:
    """Align the after raster to the before grid and calculate after - before."""
    from rasterio.warp import reproject, Resampling
    from rasterio.mask import mask as raster_mask
    from backend.utils.raster_metrics import metric_jacobian
    with rasterio.open(dsm1_path) as src1:
        if not src1.crs:
            raise ValueError('Raster anterior sem CRS')
        if aoi:
            before, transform = raster_mask(src1, [aoi['projected']], crop=True, all_touched=False,
                                             filled=False, indexes=1)
            dsm1 = before.astype(float).filled(np.nan)
        else:
            dsm1 = src1.read(1, masked=True).astype(float).filled(np.nan)
            transform = src1.transform
        profile = src1.profile.copy()
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
    diff = np.where(mask, dsm2 - dsm1, np.nan)

    for option in ('blockxsize', 'blockysize', 'tiled'):
        profile.pop(option, None)
    profile.update(dtype='float32', count=1, nodata=np.nan, width=diff.shape[1], height=diff.shape[0], transform=transform)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(diff.astype('float32'), 1)
        dst.update_tags(operation='after - before', vertical_units_assumed='m', alignment='after to before grid',
                        analysis_scope='aoi' if aoi else 'common valid area')

    valid_diff = diff[mask]

    return {
        "output_path": output_path,
        "min_diff_m": float(np.min(valid_diff)) if len(valid_diff) > 0 else 0,
        "max_diff_m": float(np.max(valid_diff)) if len(valid_diff) > 0 else 0,
        "mean_diff_m": float(np.mean(valid_diff)) if len(valid_diff) > 0 else 0,
        "std_diff_m": float(np.std(valid_diff)) if len(valid_diff) > 0 else 0,
        "pixel_area_m2": pixel_area, "valid_pixels": int(mask.sum()),
        "valid_area_m2": float(mask.sum() * pixel_area),
        "alignment": "after reprojected to before grid", "difference": "after - before",
        "vertical_units_assumed": "m",
    }

def cut_fill_analysis(dsm_before_path: str, dsm_after_path: str, output_path: str,
                      threshold: float = 0.1, aoi=None) -> dict:
    """Classify changes as cut (negative) or fill (positive)."""
    if not np.isfinite(threshold) or threshold < 0:
        raise ValueError('Limiar de mudanca deve ser finito e maior ou igual a zero')
    result = dsm_difference(dsm_before_path, dsm_after_path, output_path, aoi)

    with rasterio.open(output_path) as src:
        diff = src.read(1, masked=True).astype(float).filled(np.nan)
        mask = np.isfinite(diff)
        pixel_area_m2 = result['pixel_area_m2']

        cut_mask = mask & (diff < -threshold)
        fill_mask = mask & (diff > threshold)
        stable_mask = mask & ~(cut_mask | fill_mask)

        cut_volume = float(np.sum(np.abs(diff[cut_mask])) * pixel_area_m2)
        fill_volume = float(np.sum(diff[fill_mask]) * pixel_area_m2)
        cut_area = float(np.sum(cut_mask) * pixel_area_m2)
        fill_area = float(np.sum(fill_mask) * pixel_area_m2)
        stable_area = float(np.sum(stable_mask) * pixel_area_m2)
        changed_pixels = int(np.sum(cut_mask | fill_mask))

    result.update({
        "cut_volume_m3": round(cut_volume, 2),
        "fill_volume_m3": round(fill_volume, 2),
        "cut_area_m2": round(cut_area, 2),
        "fill_area_m2": round(fill_area, 2),
        "stable_area_m2": round(stable_area, 2),
        "net_volume_m3": round(fill_volume - cut_volume, 2),
        "changed_pixels": changed_pixels,
        "stable_pixels": int(np.sum(stable_mask)),
        "changed_percent": round(changed_pixels * 100 / result['valid_pixels'], 4),
        "change_threshold_m": threshold,
    })
    return result
