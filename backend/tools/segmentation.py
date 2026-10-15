"""Image segmentation tools."""
import numpy as np
import rasterio
import logging
from sklearn.cluster import KMeans
from backend.utils.raster_metrics import metric_jacobian

logger = logging.getLogger(__name__)

def segment_ortomapa(input_path: str, output_path: str, n_clusters: int = 7, min_size: int = 100, aoi=None) -> dict:
    """Cluster valid RGB pixels, optionally cropped and masked by an AOI."""
    if not 2 <= n_clusters <= 12:
        raise ValueError('Numero de grupos deve estar entre 2 e 12')
    with rasterio.open(input_path) as src:
        if src.count < 3:
            raise ValueError('Agrupamento espectral exige raster RGB com pelo menos tres bandas')
        if aoi:
            from rasterio.mask import mask as raster_mask
            bands, transform = raster_mask(src, [aoi['projected']], indexes=[1, 2, 3], crop=True,
                                           all_touched=False, filled=False)
        else:
            bands = src.read([1, 2, 3], masked=True)
            transform = src.transform
        profile = src.profile.copy()
        crs = src.crs
        height, width = bands.shape[1], bands.shape[2]

    values = np.asarray(bands)
    valid_2d = ~np.logical_or.reduce([np.ma.getmaskarray(band) for band in bands])
    valid_2d &= np.isfinite(values).all(axis=0)
    valid_mask = valid_2d.ravel()
    pixels = values.reshape(3, -1).T
    valid_indexes = np.flatnonzero(valid_mask)
    if valid_indexes.size < n_clusters:
        raise ValueError('Pixels validos insuficientes para o numero de grupos')

    max_samples = 100000
    rng = np.random.default_rng(42)
    if valid_indexes.size > max_samples:
        sample_indexes = rng.choice(valid_indexes, max_samples, replace=False)
    else:
        sample_indexes = valid_indexes

    if np.issubdtype(values.dtype, np.integer):
        scale = float(np.iinfo(values.dtype).max)
    else:
        maximum = float(np.nanmax(values[:, valid_2d]))
        scale = 1.0 if maximum <= 1 else maximum
    sample_norm = pixels[sample_indexes].astype(np.float32) / scale

    # KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    kmeans.fit(sample_norm)

    labels = np.zeros(height * width, dtype=np.uint8)
    chunk = 250000
    for start in range(0, valid_indexes.size, chunk):
        indexes = valid_indexes[start:start + chunk]
        labels[indexes] = kmeans.predict(pixels[indexes].astype(np.float32) / scale) + 1
    labels_2d = labels.reshape(height, width)

    for option in ('blockxsize', 'blockysize', 'tiled'):
        profile.pop(option, None)
    profile.update(dtype='uint8', count=1, nodata=0)
    profile.update(width=width, height=height, transform=transform, compress='lzw')
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(labels_2d, 1)
        dst.update_tags(operation='kmeans RGB', n_clusters=n_clusters, sample_pixels=len(sample_indexes),
                        analysis_scope='aoi' if aoi else 'full raster')

    pixel_area_m2 = abs(float(np.linalg.det(metric_jacobian(crs, transform))))

    cluster_stats = []
    for i in range(n_clusters):
        count = int(np.sum(labels_2d == (i + 1)))
        center = np.clip(kmeans.cluster_centers_[i] * scale, 0, scale)
        display = center * (255 / scale)
        cluster_stats.append({
            "cluster": i + 1,
            "pixel_count": count,
            "area_m2": round(count * pixel_area_m2, 2),
            "area_ha": round(count * pixel_area_m2 / 10000, 4),
            "center_rgb": [int(round(c)) for c in center[:3]],
            "display_rgb": [int(round(c)) for c in display[:3]],
            "percent": round(count / valid_indexes.size * 100, 4)
        })

    return {
        "output_path": output_path,
        "n_clusters": n_clusters,
        "total_valid_pixels": int(valid_indexes.size),
        "pixel_area_m2": pixel_area_m2,
        "valid_area_m2": float(valid_indexes.size * pixel_area_m2),
        "sample_pixels": int(len(sample_indexes)),
        "clusters": cluster_stats
    }
