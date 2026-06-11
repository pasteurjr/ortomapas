"""Image segmentation tools."""
import numpy as np
import rasterio
import json
import logging
from sklearn.cluster import KMeans

logger = logging.getLogger(__name__)

def segment_ortomapa(input_path: str, output_path: str, n_clusters: int = 7, min_size: int = 100) -> dict:
    """Segment ortomapa using KMeans clustering on RGB values."""
    with rasterio.open(input_path) as src:
        bands = src.read()  # (bands, height, width)
        profile = src.profile.copy()
        transform = src.transform
        crs = src.crs
        height, width = bands.shape[1], bands.shape[2]

    # Reshape to (pixels, bands)
    n_bands = bands.shape[0]
    pixels = bands.reshape(n_bands, -1).T.astype(float)

    # Remove nodata/zero pixels for clustering
    valid_mask = np.all(pixels > 0, axis=1)
    valid_pixels = pixels[valid_mask]

    # Subsample if too many pixels (KMeans is slow on large data)
    max_samples = 100000
    if len(valid_pixels) > max_samples:
        indices = np.random.choice(len(valid_pixels), max_samples, replace=False)
        sample = valid_pixels[indices]
    else:
        sample = valid_pixels

    # Normalize
    sample_norm = sample / 255.0

    # KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10, max_iter=300)
    kmeans.fit(sample_norm)

    # Predict all valid pixels
    all_norm = valid_pixels / 255.0
    labels_valid = kmeans.predict(all_norm)

    # Reconstruct full label image
    labels = np.zeros(height * width, dtype=np.uint8)
    labels[valid_mask] = labels_valid + 1  # 0 = nodata, 1-N = clusters
    labels_2d = labels.reshape(height, width)

    # Write classified raster
    profile.update(dtype='uint8', count=1, nodata=0)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(labels_2d, 1)

    # Compute statistics per cluster
    pixel_width = abs(transform[0])
    pixel_height = abs(transform[4])
    if crs and crs.is_geographic:
        center_lat = (rasterio.open(input_path).bounds.top + rasterio.open(input_path).bounds.bottom) / 2
        meter_per_deg_lon = 111320 * np.cos(np.radians(center_lat))
        meter_per_deg_lat = 110540
        pixel_area_m2 = (pixel_width * meter_per_deg_lon) * (pixel_height * meter_per_deg_lat)
    else:
        pixel_area_m2 = pixel_width * pixel_height

    cluster_stats = []
    for i in range(n_clusters):
        count = int(np.sum(labels_2d == (i + 1)))
        center = kmeans.cluster_centers_[i] * 255
        cluster_stats.append({
            "cluster": i + 1,
            "pixel_count": count,
            "area_m2": round(count * pixel_area_m2, 2),
            "area_ha": round(count * pixel_area_m2 / 10000, 4),
            "center_rgb": [int(c) for c in center[:3]] if len(center) >= 3 else [int(c) for c in center],
            "percent": round(count / max(np.sum(valid_mask), 1) * 100, 2)
        })

    return {
        "output_path": output_path,
        "n_clusters": n_clusters,
        "total_valid_pixels": int(np.sum(valid_mask)),
        "clusters": cluster_stats
    }
