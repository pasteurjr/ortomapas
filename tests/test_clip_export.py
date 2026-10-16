import json
import shutil
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

from backend.utils.clip_export import clip_raster_aoi, export_dataset


@pytest.fixture
def raster(tmp_path):
    source = tmp_path / 'source.tif'
    with rasterio.open(source, 'w', driver='GTiff', width=20, height=20, count=1,
                       dtype='uint8', crs='EPSG:32624', transform=from_origin(500000, 8600000, 1, 1)) as ds:
        ds.write(np.arange(400, dtype='uint8').reshape(20, 20), 1)
    return source


def test_clip_masks_polygon_and_preserves_georeference(raster, tmp_path):
    target = tmp_path / 'clip.tif'
    polygon = mapping(box(500002, 8599982, 500018, 8599998).difference(box(500008, 8599988, 500012, 8599992)))
    stats = clip_raster_aoi(raster, target, polygon)
    with rasterio.open(target) as ds:
        assert ds.crs.to_epsg() == 32624
        assert (ds.width, ds.height) == (16, 16)
        assert stats['valid_pixels'] == 240
        assert ds.dataset_mask()[8, 8] == 0
        assert ds.dataset_mask()[1, 1] == 255
        with rasterio.open(raster) as original:
            np.testing.assert_array_equal(ds.read(1)[1:3, 1:3], original.read(1)[3:5, 3:5])


def test_clip_real_rgb_orthophoto(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'data/ortomapas/rasterio_rgb_f866f21d.tif'
    if not source.exists():
        pytest.skip('Ortofoto real nao disponivel nesta instalacao')
    with rasterio.open(source) as ds:
        bounds = ds.bounds
        polygon = mapping(box(bounds.left + ds.res[0] * 100, bounds.bottom + ds.res[1] * 100,
                              bounds.right - ds.res[0] * 100, bounds.top - ds.res[1] * 100))
        original_pixel = ds.read(1, window=((200, 201), (200, 201)))[0, 0]
    target = tmp_path / 'real_clip.tif'
    stats = clip_raster_aoi(source, target, polygon)
    with rasterio.open(target) as ds:
        assert ds.count == 3 and ds.crs.to_epsg() == 32618
        assert stats['valid_pixels'] > 0
        assert ds.read(1)[100, 100] == original_pixel
        assert ds.dataset_mask().any()


@pytest.mark.skipif(not shutil.which('gdalwarp'), reason='GDAL CLI required')
def test_export_raster_reprojects_and_rejects_vector_format(raster, tmp_path):
    target = tmp_path / 'export.tif'
    export_dataset(raster, 'geotiff', 'EPSG:4326', target)
    with rasterio.open(target) as ds:
        assert ds.crs.to_epsg() == 4326
        assert ds.dataset_mask().any()
    with pytest.raises(ValueError, match='incompativel'):
        export_dataset(raster, 'kml', 'EPSG:4326', tmp_path / 'wrong.kml')


@pytest.mark.skipif(not shutil.which('ogr2ogr'), reason='OGR CLI required')
def test_export_vector_kml_and_shapefile(tmp_path):
    source = tmp_path / 'source.geojson'
    source.write_text(json.dumps({'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'properties': {'id': 1},
         'geometry': {'type': 'Point', 'coordinates': [-38.7, -12.65]}}]}))
    kml = tmp_path / 'export.kml'
    export_dataset(source, 'kml', 'EPSG:4326', kml)
    assert '<kml' in kml.read_text()
    archive = tmp_path / 'export.zip'
    export_dataset(source, 'shapefile', 'EPSG:31984', archive)
    with zipfile.ZipFile(archive) as zipped:
        assert {'camada.shp', 'camada.dbf', 'camada.shx', 'camada.prj'} <= set(zipped.namelist())
    with pytest.raises(ValueError, match='EPSG:4326'):
        export_dataset(source, 'geojson', 'EPSG:31984', tmp_path / 'wrong.geojson')
