import numpy as np
import pytest
import rasterio
from affine import Affine
from pyproj import Transformer
from shapely.geometry import box, mapping
from shapely.ops import transform

from backend.routers.tools import DSMDiffRequest
from backend.tools.volumetry import cut_fill_analysis
from backend.utils.analysis_products import STYLES, colorize
from backend.utils.terrain_aoi import prepare_aoi


def raster(path, values, grid=Affine(1, 0, 500000, 0, -1, 4600000), crs='EPSG:32617'):
    with rasterio.open(path, 'w', driver='GTiff', width=values.shape[1], height=values.shape[0],
                       count=1, dtype='float32', crs=crs, transform=grid, nodata=-9999) as ds:
        ds.write(values.astype('float32'), 1)
    return path


def aoi_for(path, polygon):
    geometry = transform(Transformer.from_crs(32617, 4326, always_xy=True).transform, polygon)
    return prepare_aoi(str(path), mapping(geometry))


def test_known_cut_fill_threshold_and_sign(tmp_path):
    before = raster(tmp_path / 'before.tif', np.full((10, 10), 100.0))
    after_values = np.full((10, 10), 100.05)
    after_values[:4] = 102.0
    after_values[4:7] = 97.0
    after = raster(tmp_path / 'after.tif', after_values)
    output = tmp_path / 'difference.tif'

    result = cut_fill_analysis(str(before), str(after), str(output), threshold=0.1)

    assert result['fill_volume_m3'] == 80.0
    assert result['cut_volume_m3'] == 90.0
    assert result['net_volume_m3'] == -10.0
    assert result['fill_area_m2'] == 40.0
    assert result['cut_area_m2'] == 30.0
    assert result['stable_area_m2'] == 30.0
    assert result['changed_percent'] == 70.0
    assert result['difference'] == 'after - before'
    with rasterio.open(output) as ds:
        values = ds.read(1, masked=True)
        assert ds.nodata != -9999
        assert values[0, 0] == pytest.approx(2)
        assert values[5, 0] == pytest.approx(-3)
        assert values[9, 0] == pytest.approx(0.05, abs=1e-4)


def test_aoi_excludes_changes_outside_polygon(tmp_path):
    before = raster(tmp_path / 'before.tif', np.full((20, 20), 100.0))
    after_values = np.full((20, 20), 999.0)
    after_values[5:15, 5:15] = 101.0
    after = raster(tmp_path / 'after.tif', after_values)
    aoi = aoi_for(before, box(500005, 4599985, 500015, 4599995))

    result = cut_fill_analysis(str(before), str(after), str(tmp_path / 'aoi.tif'), 0.1, aoi)

    assert result['valid_pixels'] == 100
    assert result['valid_area_m2'] == 100
    assert result['fill_volume_m3'] == 100
    assert result['cut_volume_m3'] == 0
    with rasterio.open(tmp_path / 'aoi.tif') as ds:
        assert ds.width < 20 and ds.height < 20
        assert ds.read(1, masked=True).count() == 100


def test_after_is_reprojected_to_before_grid(tmp_path):
    before = raster(tmp_path / 'before.tif', np.full((4, 4), 10.0), Affine(2, 0, 500000, 0, -2, 4600000))
    after = raster(tmp_path / 'after.tif', np.full((8, 8), 11.0), Affine(1, 0, 500000, 0, -1, 4600000))

    result = cut_fill_analysis(str(before), str(after), str(tmp_path / 'aligned.tif'), 0.1)

    assert result['valid_pixels'] == 16
    assert result['pixel_area_m2'] == 4
    assert result['fill_volume_m3'] == 64
    assert result['alignment'] == 'after reprojected to before grid'


def test_no_common_valid_area_is_rejected(tmp_path):
    before = raster(tmp_path / 'before.tif', np.ones((2, 2)), Affine(1, 0, 500000, 0, -1, 4600000))
    after = raster(tmp_path / 'after.tif', np.ones((2, 2)), Affine(1, 0, 600000, 0, -1, 4700000))
    with pytest.raises(ValueError, match='sem area comum valida'):
        cut_fill_analysis(str(before), str(after), str(tmp_path / 'none.tif'))


@pytest.mark.parametrize('threshold', [-1, float('nan'), float('inf')])
def test_invalid_threshold_is_rejected(tmp_path, threshold):
    before = raster(tmp_path / 'before.tif', np.ones((2, 2)))
    after = raster(tmp_path / 'after.tif', np.ones((2, 2)))
    with pytest.raises(ValueError):
        cut_fill_analysis(str(before), str(after), str(tmp_path / 'invalid.tif'), threshold)


def test_request_requires_finite_nonnegative_threshold():
    valid = dict(dsm1_path='before.tif', dsm2_path='after.tif', output_name='diff',
                 ortomapa_antes_id=1, ortomapa_depois_id=2, projeto_id=3)
    assert DSMDiffRequest(**valid).threshold == 0.1
    for threshold in (-1, float('nan'), float('inf')):
        with pytest.raises(ValueError):
            DSMDiffRequest(**valid, threshold=threshold)


def test_change_colors_preserve_stable_band_and_sign():
    style = {**STYLES['elevation_change'], 'min': -2, 'max': 2, 'threshold': 0.1}
    values = np.array([[-2.0, -0.1, 0, 0.1, 2.0]])
    rgba = colorize(values, np.ones(values.shape, bool), style)
    assert np.array_equal(rgba[0, 0], [178, 24, 43, 255])
    assert np.array_equal(rgba[0, 1], [247, 247, 247, 0])
    assert np.array_equal(rgba[0, 2], [247, 247, 247, 0])
    assert np.array_equal(rgba[0, 3], [247, 247, 247, 0])
    assert np.array_equal(rgba[0, 4], [33, 102, 172, 255])
