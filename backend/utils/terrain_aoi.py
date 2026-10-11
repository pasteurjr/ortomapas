"""Validate WGS84 analysis areas and mask derivatives without edge gradients."""
import json
import os
import tempfile
from pathlib import Path

import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.features import geometry_window
from rasterio.mask import mask
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely.errors import GEOSException

from backend.utils.raster_metrics import metric_jacobian


def prepare_aoi(input_path, geometry):
    if geometry is None:
        return None
    try:
        if geometry.get('type') not in {'Polygon', 'MultiPolygon'}:
            raise ValueError('A area deve ser um Polygon ou MultiPolygon GeoJSON em WGS84')
        polygon = shape(geometry)
        if polygon.is_empty or not polygon.is_valid or polygon.area <= 0:
            raise ValueError('Poligono vazio, degenerado ou com intersecoes invalidas')
        from shapely import get_coordinates
        coordinates = get_coordinates(polygon)
        if len(coordinates) > 2000 or not np.isfinite(coordinates).all():
            raise ValueError('Area excede 2000 vertices ou contem coordenadas invalidas')
        if (np.abs(coordinates[:, 0]) > 180).any() or (np.abs(coordinates[:, 1]) > 90).any():
            raise ValueError('Coordenadas da area devem estar em WGS84')
        if polygon.bounds[2] - polygon.bounds[0] > 180:
            raise ValueError('Areas cruzando o antimeridiano nao sao suportadas')
        with rasterio.open(input_path) as ds:
            matrix = metric_jacobian(ds.crs, ds.transform)
            projected = transform(Transformer.from_crs(4326, ds.crs, always_xy=True).transform, polygon)
            if not projected.is_valid or not np.isfinite(projected.bounds).all():
                raise ValueError('Area invalida apos reprojecao')
            geometry_window(ds, [mapping(projected)])
            conversion = abs(np.linalg.det(matrix) / (ds.transform.a*ds.transform.e-ds.transform.b*ds.transform.d))
            return {'geometry': mapping(polygon), 'projected': mapping(projected),
                    'area_m2': projected.area * conversion,
                    'pixel_area_m2': abs(float(np.linalg.det(matrix)))}
    except (TypeError, KeyError, AttributeError, GEOSException, rasterio.errors.WindowError) as exc:
        raise ValueError('Area invalida ou sem intersecao com o modelo') from exc


def mask_derivative(path, aoi):
    if aoi is None:
        return
    with rasterio.open(path) as ds:
        values, affine = mask(ds, [aoi['projected']], crop=True, all_touched=False, filled=False)
        valid = ~np.ma.getmaskarray(values[0]) & np.isfinite(values[0].data)
        if not valid.any():
            raise ValueError('Area sem pixels validos para esta analise')
        profile = ds.profile.copy()
        profile.update(width=values.shape[2], height=values.shape[1], transform=affine, nodata=-9999)
        tags = ds.tags()
    # Replace only a completely written GeoTIFF; never edit an open raster in place.
    fd, temporary = tempfile.mkstemp(suffix='.tif', dir=Path(path).parent)
    os.close(fd)
    try:
        with rasterio.open(temporary, 'w', **profile) as dst:
            dst.write(values.filled(-9999))
            dst.update_tags(**tags, analysis_scope='aoi', aoi_wgs84=json.dumps(aoi['geometry']))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
