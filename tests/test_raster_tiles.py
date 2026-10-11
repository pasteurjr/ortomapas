"""Regression checks for the spatial placement, transparency and stable XYZ scaling."""

import io

import numpy as np
import pytest
import rasterio
from PIL import Image
from rasterio.enums import ColorInterp
from rasterio.transform import from_bounds

from backend.utils.raster_tiles import render_xyz_tile, tile_bounds


def write_raster(path, data, bounds, nodata=None, alpha=False, crs="EPSG:3857"):
    with rasterio.open(path, "w", driver="GTiff", width=data.shape[2], height=data.shape[1], count=data.shape[0], dtype=data.dtype, crs=crs, transform=from_bounds(*bounds, data.shape[2], data.shape[1]), nodata=nodata) as ds:
        ds.write(data)
        if alpha:
            ds.colorinterp = (ColorInterp.red, ColorInterp.green, ColorInterp.blue, ColorInterp.alpha)


def rgba(path, z=2, x=1, y=1):
    return np.array(Image.open(io.BytesIO(render_xyz_tile(path, z, x, y))).convert("RGBA"))


def test_partial_raster_preserves_empty_half(tmp_path):
    left, bottom, right, top = tile_bounds(2, 1, 1)
    path = tmp_path / "half.tif"
    write_raster(path, np.full((3, 256, 128), 180, dtype=np.uint8), (left, bottom, (left + right) / 2, top))
    tile = rgba(path)
    assert tile.shape == (256, 256, 4)
    assert np.all(tile[:, :128, :3] == 180)
    assert np.all(tile[:, :128, 3] == 255)
    assert np.all(tile[:, 128:, 3] == 0)


def test_black_is_valid_without_nodata(tmp_path):
    path = tmp_path / "black.tif"
    write_raster(path, np.zeros((3, 256, 256), dtype=np.uint8), tile_bounds(2, 1, 1))
    assert np.all(rgba(path)[:, :, 3] == 255)


def test_alpha_hole_is_transparent(tmp_path):
    data = np.full((4, 256, 256), 255, dtype=np.uint8)
    data[3, 64:192, 64:192] = 0
    path = tmp_path / "alpha.tif"
    write_raster(path, data, tile_bounds(2, 1, 1), alpha=True)
    tile = rgba(path)
    assert np.all(tile[64:192, 64:192, 3] == 0)
    assert tile[0, 0, 3] == 255


def test_nodata_is_transparent_and_neighbors_stay_visible(tmp_path):
    data = np.full((1, 256, 256), 90, dtype=np.float32)
    data[:, :100, :100] = -9999
    path = tmp_path / "nodata.tif"
    write_raster(path, data, tile_bounds(2, 1, 1), nodata=-9999)
    tile = rgba(path)
    assert np.all(tile[:100, :100, 3] == 0)
    assert tile[200, 200, 3] == 255


def test_outside_returns_fully_transparent(tmp_path):
    path = tmp_path / "outside.tif"
    write_raster(path, np.ones((3, 256, 256), dtype=np.uint8), tile_bounds(2, 1, 1))
    assert not rgba(path, x=3, y=3).any()


def test_float_tiles_use_one_source_wide_scale(tmp_path):
    left, bottom, _, top = tile_bounds(2, 1, 1)
    right = tile_bounds(2, 2, 1)[2]
    data = np.broadcast_to(np.arange(512, dtype=np.float32), (1, 256, 512)).copy()
    path = tmp_path / "gradient.tif"
    write_raster(path, data, (left, bottom, right, top))
    first, second = rgba(path), rgba(path, x=2)
    assert first[128, 255, 0] <= 128
    assert second[128, 0, 0] >= 127
    assert abs(int(first[128, 255, 0]) - int(second[128, 0, 0])) <= 1
    assert second[128, 255, 0] == 255


@pytest.mark.parametrize("coords", [(-1, 0, 0), (23, 0, 0), (2, -1, 0), (2, 4, 0), (2, 0, 4)])
def test_invalid_xyz_rejected(coords):
    with pytest.raises(ValueError):
        tile_bounds(*coords)
