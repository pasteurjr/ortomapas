import numpy as np
import pytest
from affine import Affine
from shapely.geometry import Point, Polygon, mapping, shape

from backend.utils.spatial_metrics import geometry_metrics
from backend.utils.raster_metrics import terrain_gradient, volume_metrics


def test_projected_rectangle_and_distance():
    polygon = mapping(Polygon([(500000, 8600000), (500100, 8600000), (500100, 8600200), (500000, 8600200)]))
    result = geometry_metrics('medir_geometria', {'geometry': polygon, 'crs': 'EPSG:32724'})
    assert result['area_m2'] == 20000
    assert result['perimetro_m'] == 600
    distance = geometry_metrics('distancia_geometrias', {'a': mapping(Point(0, 0)), 'b': mapping(Point(3, 4)), 'crs': 'EPSG:32724'})
    assert distance['distancia_m'] == 5


def test_guarajuba_buffer_is_metres_not_degrees():
    point = mapping(Point(-38.046, -12.654))
    result = geometry_metrics('buffer_geometria', {'geometry': point, 'distancia': 100})
    assert result['crs_saida'] == 'EPSG:4326'
    assert result['crs_calculo'] == 'EPSG:32724'
    polygon = shape(result['geometry'])
    assert polygon.bounds[2]-polygon.bounds[0] < .003
    area = geometry_metrics('medir_geometria', {'geometry': result['geometry']})['area_m2']
    assert area == pytest.approx(np.pi*100**2, rel=.002)


def test_invalid_or_global_geometries_rejected():
    with pytest.raises(ValueError):
        geometry_metrics('buffer_geometria', {'geometry': mapping(Point(0, 0)), 'distancia': -1})
    with pytest.raises(ValueError):
        geometry_metrics('medir_geometria', {'geometry': mapping(Polygon([(-170,0),(170,0),(170,10),(-170,10)]))})


@pytest.mark.parametrize('affine', [Affine(2,0,0,0,-3,0), Affine(2,1,0,1,-3,0)])
def test_slope_known_plane_and_sampled_resolution(affine):
    for factor in (1, 4):
        grid = affine * Affine.scale(factor)
        row, col = np.indices((10, 15))
        east = grid.a*col + grid.b*row
        north = grid.d*col + grid.e*row
        gx, gy, valid = terrain_gradient(.5*east+.25*north, 'EPSG:32724', grid)
        assert valid.all()
        assert np.allclose(gx, .5)
        assert np.allclose(gy, .25)
        assert np.allclose(np.degrees(np.arctan(np.hypot(gx,gy))), 29.205932247399414)


def test_volume_rotated_grid_and_nodata():
    grid = Affine(2,1,0,1,-3,0)  # determinant -7 => 7 m2 per cell
    values = np.ma.array([[12., 8.], [np.nan, 15.]], mask=[[False,False],[True,False]])
    result = volume_metrics(values, 'EPSG:32724', grid, 10.)
    assert result['pixel_area_m2'] == pytest.approx(7)
    assert result['volume_above_m3'] == pytest.approx(49)
    assert result['volume_below_m3'] == pytest.approx(14)


def test_geographic_raster_not_labelled_metric():
    with pytest.raises(ValueError, match='Reprojete'):
        volume_metrics(np.ones((2,2)), 'EPSG:4326', Affine.scale(.001), 0.)


def test_feet_projected_units_converted():
    result = volume_metrics(np.ones((2,2)), 'EPSG:2263', Affine.scale(10), 0.)
    assert result['volume_above_m3'] == pytest.approx(400*(1200/3937)**2)


def test_tools_share_metric_engine_and_preserve_output_nodata(tmp_path):
    import rasterio
    from backend.tools.raster_analysis import calc_slope
    from backend.tools.volumetry import calc_volume
    source, slope, delta = [tmp_path/name for name in ('dem.tif','slope.tif','delta.tif')]
    row, col = np.indices((6,6))
    grid = Affine(2,0,500000,0,-2,8600000)
    dem = (100 + col).astype('float32')
    dem[0,0] = -9999
    with rasterio.open(source,'w',driver='GTiff',width=6,height=6,count=1,dtype='float32',crs='EPSG:32724',transform=grid,nodata=-9999) as ds:
        ds.write(dem,1)
    calc_slope(str(source),str(slope))
    with rasterio.open(slope) as ds:
        assert np.allclose(ds.read(1,masked=True).compressed(), np.degrees(np.arctan(.5)))
    actual = calc_volume(str(source),100.,str(delta))
    assert actual['volume_above_m3'] == 360
    with rasterio.open(delta) as ds:
        assert ds.read(1,masked=True).mask[0,0]
