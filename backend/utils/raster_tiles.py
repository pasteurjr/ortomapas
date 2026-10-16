"""Georeferenced XYZ rendering on the complete tile grid, including empty margins."""

import io
import os
from functools import lru_cache

import numpy as np
import rasterio
from PIL import Image
from rasterio.enums import ColorInterp, Resampling
from rasterio.transform import from_bounds
from rasterio.vrt import WarpedVRT

TILE_SIZE = 256
WORLD = 20037508.342789244


def tile_bounds(z: int, x: int, y: int) -> tuple:
    if not 0 <= z <= 22 or not 0 <= x < 2 ** z or not 0 <= y < 2 ** z:
        raise ValueError("Coordenadas XYZ fora do intervalo permitido")
    span = 2 * WORLD / 2 ** z
    left, top = -WORLD + x * span, WORLD - y * span
    return left, top - span, left + span, top


@lru_cache(maxsize=64)
def _display_range(path: str, mtime_ns: int, size: int, indexes: tuple) -> tuple:
    # One source-wide stretch prevents visible seams between neighboring tiles.
    with rasterio.open(path) as source:
        sample = source.read(indexes, out_shape=(len(indexes), min(512, source.height), min(512, source.width)), masked=True)
    values = sample.compressed()
    values = values[np.isfinite(values)]
    if not values.size:
        return 0.0, 0.0
    return float(values.min()), float(values.max())


def render_xyz_tile(path: str, z: int, x: int, y: int) -> bytes:
    bounds = tile_bounds(z, x, y)
    with rasterio.open(path) as source:
        if source.crs is None:
            raise ValueError("Raster sem sistema de coordenadas")
        indexes = tuple(i + 1 for i, color in enumerate(source.colorinterp) if color != ColorInterp.alpha)
        indexes = indexes[:3] if len(indexes) >= 3 else indexes[:1]
        with WarpedVRT(
            source,
            crs="EPSG:3857",
            transform=from_bounds(*bounds, TILE_SIZE, TILE_SIZE),
            width=TILE_SIZE,
            height=TILE_SIZE,
            resampling=Resampling.bilinear,
            add_alpha=ColorInterp.alpha not in source.colorinterp,
            warp_extras={"INIT_DEST": "0"},
        ) as tile:
            data = tile.read(indexes)
            # Float alpha bands are not always reflected in GDAL dataset_mask.
            alpha_index = tile.colorinterp.index(ColorInterp.alpha) + 1
            alpha_values = tile.read(alpha_index)
            if np.issubdtype(alpha_values.dtype, np.integer) and alpha_values.dtype != np.uint8:
                alpha_values = alpha_values.astype(np.float64) * (255 / np.iinfo(alpha_values.dtype).max)
            alpha = np.nan_to_num(np.clip(alpha_values, 0, 255)).astype(np.uint8)
        alpha[~np.isfinite(data).all(axis=0)] = 0
        if data.dtype != np.uint8:
            stat = os.stat(path)
            low, high = _display_range(str(path), stat.st_mtime_ns, stat.st_size, indexes)
            if high > low:
                data = np.nan_to_num(np.clip((data.astype(np.float64) - low) * (255 / (high - low)), 0, 255)).astype(np.uint8)
            else:
                data = np.zeros(data.shape, dtype=np.uint8)
        if len(indexes) == 1:
            data = np.repeat(data, 3, axis=0)
        rgba = np.dstack((data.transpose(1, 2, 0), alpha))
        rgba[alpha == 0, :3] = 0
    output = io.BytesIO()
    Image.fromarray(rgba).save(output, format="PNG")
    return output.getvalue()


def render_analysis_tile(path, z, x, y, style):
    if style.get('kind') == 'raw':
        return render_xyz_tile(path, z, x, y)
    from backend.utils.analysis_products import colorize
    from rasterio.warp import reproject
    bounds=tile_bounds(z,x,y)
    with rasterio.open(path) as source:
        if not source.crs:
            raise ValueError('Raster sem CRS')
        data=np.full((TILE_SIZE,TILE_SIZE),np.nan,dtype='float32')
        reproject(rasterio.band(source,1),data,src_transform=source.transform,src_crs=source.crs,
                  src_nodata=source.nodata,dst_transform=from_bounds(*bounds,TILE_SIZE,TILE_SIZE),
                  dst_crs='EPSG:3857',dst_nodata=np.nan,
                  resampling=Resampling.nearest if style['method']=='nearest' else Resampling.bilinear)
    rgba=colorize(data,np.isfinite(data),style)
    output=io.BytesIO();Image.fromarray(rgba).save(output,format='PNG')
    return output.getvalue()
