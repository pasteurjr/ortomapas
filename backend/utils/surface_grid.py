"""Sample terrain with metric horizontal coordinates and explicit nodata holes."""
import numpy as np
import rasterio
from affine import Affine
from pyproj import CRS, Transformer
from rasterio.enums import Resampling


def metric_surface(path, max_size=128):
    with rasterio.open(path) as ds:
        if not ds.crs:
            raise ValueError("Raster sem CRS; nao e possivel determinar unidades")
        scale = min(1, max_size / max(ds.width, ds.height))
        width, height = max(2, round(ds.width * scale)), max(2, round(ds.height * scale))
        if ds.width < 2 or ds.height < 2:
            raise ValueError("Raster precisa de pelo menos duas linhas e duas colunas")
        grid = ds.read(1, out_shape=(height, width), resampling=Resampling.bilinear, masked=True).astype(np.float64)
        values = np.asarray(grid.filled(np.nan), dtype=float)
        valid = np.isfinite(values) & ~np.ma.getmaskarray(grid)
        if not valid.any():
            raise ValueError("Raster nao possui elevacoes validas")
        transform = ds.transform * Affine.scale(ds.width / width, ds.height / height)
        row, col = np.indices((height, width))
        xs = transform.a * (col + .5) + transform.b * (row + .5) + transform.c
        ys = transform.d * (col + .5) + transform.e * (row + .5) + transform.f
        source_crs = CRS.from_user_input(ds.crs)
        if source_crs.is_projected and all(abs(axis.unit_conversion_factor - 1) < 1e-9 for axis in source_crs.axis_info[:2]):
            metric_crs = source_crs
        else:
            lon, lat = Transformer.from_crs(source_crs, 4326, always_xy=True).transform(float(xs.mean()), float(ys.mean()))
            if not -80 <= lat <= 84:
                raise ValueError("Extensao fora do dominio UTM")
            zone = min(60, max(1, int((lon + 180) / 6) + 1))
            metric_crs = CRS.from_epsg((32600 if lat >= 0 else 32700) + zone)
            xs, ys = Transformer.from_crs(source_crs, metric_crs, always_xy=True).transform(xs, ys)
        origin = [float(xs.mean()), float(ys.mean()), float(values[valid].min())]
        elevations = [[float(values[r, c]) if valid[r, c] else None for c in range(width)] for r in range(height)]
        return {"width": width, "height": height, "bounds": list(ds.bounds), "crs": str(ds.crs), "metric_crs": metric_crs.to_string(), "units": "m", "origin": origin, "x": (xs - origin[0]).tolist(), "y": (ys - origin[1]).tolist(), "min": origin[2], "max": float(values[valid].max()), "elevations": elevations}
