import numpy as np
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import Polygon, mapping, box
from shapely.ops import transform

from backend.tools.raster_analysis import calc_slope
from backend.utils.terrain_aoi import prepare_aoi, mask_derivative


@pytest.fixture
def model(tmp_path):
    path = tmp_path/'model.tif'
    row, col = np.indices((100, 100))
    with rasterio.open(path, 'w', driver='GTiff', width=100, height=100, count=1,
                       dtype='float32', crs='EPSG:32617', transform=from_origin(436900,4572850,1,1), nodata=-9999) as ds:
        ds.write((240 + col*.1 + row*.2).astype('float32'), 1)
    return path


def wgs(polygon):
    return mapping(transform(Transformer.from_crs(32617,4326,always_xy=True).transform,polygon))


def test_known_area_and_gradient_context(model,tmp_path):
    output=tmp_path/'slope.tif'
    aoi=prepare_aoi(model,wgs(box(436920,4572790,436940,4572820)))
    calc_slope(model,output)
    mask_derivative(output,aoi)
    with rasterio.open(output) as ds:
        values=ds.read(1,masked=True)
        assert values.count()==600
        assert ds.crs.to_epsg()==32617
        assert ds.res==(1,1)
        assert np.allclose(values.compressed(),np.degrees(np.arctan(np.hypot(.1,.2))),atol=.001)
        assert ds.tags()['analysis_scope']=='aoi'
    assert aoi['area_m2']==pytest.approx(600,abs=.001)
    assert aoi['pixel_area_m2']==pytest.approx(1)


def test_polygon_hole_is_not_bbox(model,tmp_path):
    polygon=Polygon([(436920,4572790),(436950,4572790),(436950,4572820),(436920,4572820)],
                    holes=[[(436930,4572800),(436940,4572800),(436940,4572810),(436930,4572810)]])
    output=tmp_path/'hole.tif';calc_slope(model,output)
    mask_derivative(output,prepare_aoi(model,wgs(polygon)))
    with rasterio.open(output) as ds:
        assert ds.read(1,masked=True).count()==800


@pytest.mark.parametrize('geometry',[
    {'type':'Point','coordinates':[-81,41]},
    {'type':'Polygon','coordinates':[]},
    {'type':'Polygon','coordinates':[[[0,0],[1,1],[1,0],[0,1],[0,0]]]},
    {'type':'Polygon','coordinates':[[[181,0],[182,0],[182,1],[181,0]]]},
    {'type':'Polygon','coordinates':[[[0,0],[1,0],[1,1],[0,0]]]},
])
def test_invalid_or_outside_aoi_rejected(model,geometry):
    with pytest.raises(ValueError): prepare_aoi(model,geometry)


def test_no_valid_pixels_rejected(model,tmp_path):
    output=tmp_path/'flat.tif'
    with rasterio.open(model) as ds: profile=ds.profile
    with rasterio.open(output,'w',**profile) as ds: ds.write(np.full((100,100),-9999,dtype='float32'),1)
    with pytest.raises(ValueError,match='sem pixels validos'):
        mask_derivative(output,prepare_aoi(model,wgs(box(436920,4572790,436940,4572820))))


def test_full_raster_compatibility(model):
    assert prepare_aoi(model,None) is None
    assert mask_derivative(model,None) is None
