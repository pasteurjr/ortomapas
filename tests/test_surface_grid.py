import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from backend.utils.surface_grid import metric_surface


def raster(path, crs="EPSG:32617", hole=False):
    values = np.arange(2000, dtype=np.float32).reshape(20, 100) / 100
    if hole:
        values[5:10, 20:30] = -9999
    with rasterio.open(path, "w", driver="GTiff", width=100, height=20, count=1, dtype="float32", crs=crs, transform=from_origin(436850, 4572900, 2, 2), nodata=-9999) as ds:
        ds.write(values, 1)


def test_grid_keeps_aspect_and_metric_spacing_after_sampling(tmp_path):
    path = tmp_path / "surface.tif"; raster(path)
    data = metric_surface(path, 50)
    assert (data["width"], data["height"]) == (50, 10)
    assert data["units"] == "m"
    assert data["x"][0][1] - data["x"][0][0] == pytest.approx(4)
    assert data["y"][1][0] - data["y"][0][0] == pytest.approx(-4)


def test_grid_preserves_nodata_as_null_not_flat_floor(tmp_path):
    path = tmp_path / "hole.tif"; raster(path, hole=True)
    data = metric_surface(path)
    assert data["elevations"][7][25] is None
    assert data["elevations"][0][0] is not None


def test_missing_crs_is_rejected(tmp_path):
    path = tmp_path / "unknown.tif"; raster(path, crs=None)
    with pytest.raises(ValueError, match="CRS"):
        metric_surface(path)


def test_geographic_grid_transforms_to_metric_utm(tmp_path):
    path = tmp_path / "wgs84.tif"
    with rasterio.open(path, "w", driver="GTiff", width=10, height=10, count=1, dtype="float32", crs="EPSG:4326", transform=from_origin(-81.75, 41.305, .00001, .00001)) as ds:
        ds.write(np.ones((10, 10), dtype=np.float32), 1)
    data = metric_surface(path)
    assert data["metric_crs"] == "EPSG:32617"
    assert .8 < data["x"][0][1] - data["x"][0][0] < .9
