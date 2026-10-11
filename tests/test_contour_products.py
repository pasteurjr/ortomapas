import json
import shutil

import numpy as np
import pytest
import rasterio
from pyproj import Transformer
from rasterio.transform import from_origin
from shapely.geometry import box, shape

from backend.tools.gdal_tools import generate_contours
from backend.utils.contour_products import contour_result, contour_input
from backend.routers.tools import ContourRequest


@pytest.fixture
def plane(tmp_path):
    if not shutil.which('gdal_contour'): pytest.skip('GDAL CLI required')
    path=tmp_path/'plane.tif';row,col=np.indices((100,100))
    with rasterio.open(path,'w',driver='GTiff',width=100,height=100,count=1,dtype='float32',
                       crs='EPSG:32617',transform=from_origin(436900,4572850,1,1),nodata=-9999) as ds:
        ds.write((200+.1*col+.2*row).astype('float32'),1)
    return path


def test_gdal_contours_positions_and_elevations(plane,tmp_path):
    output=tmp_path/'lines.geojson';generate_contours(str(plane),str(output),interval=5)
    result=contour_result(output,'EPSG:32617',5)
    collection=json.loads(output.read_text())
    assert collection['type']=='FeatureCollection' and 'crs' not in collection
    assert result['stats']['feature_count']>0
    checked=0;back=Transformer.from_crs(4326,32617,always_xy=True)
    for feature in collection['features']:
        elevation=feature['properties']['elevation_m']
        assert elevation%5==pytest.approx(0)
        assert feature['properties']['major']==(elevation%25==0)
        for lon,lat in feature['geometry']['coordinates']:
            assert -180<=lon<=180 and -90<=lat<=90
            x,y=back.transform(lon,lat)
            if 436900.5<x<436999.5 and 4572750.5<y<4572849.5:
                expected=200+.1*(x-436900-.5)+.2*(4572850-y-.5)
                assert abs(elevation-expected)<.001
                checked+=1
    assert checked>100


def test_vector_clip_uses_polygon_not_its_bbox(plane,tmp_path):
    output=tmp_path/'clip.geojson';generate_contours(str(plane),str(output),interval=1)
    polygon=box(436910,4572770,436980,4572830).difference(box(436935,4572790,436955,4572810))
    result=contour_result(output,'EPSG:32617',1,{'projected':polygon.__geo_interface__,'geometry':{},'area_m2':polygon.area})
    back=Transformer.from_crs(4326,32617,always_xy=True)
    from shapely.ops import transform
    for feature in result['geojson']['features']:
        assert polygon.buffer(.000001).covers(transform(back.transform,shape(feature['geometry'])))


def test_empty_result_is_explicit_error(tmp_path):
    path=tmp_path/'empty.geojson';path.write_text(json.dumps({'type':'FeatureCollection','features':[]}))
    with pytest.raises(ValueError,match='Nenhuma curva'): contour_result(path,'EPSG:32617',5)


def test_window_with_halo_preserves_contours_inside_aoi(plane,tmp_path):
    from shapely.ops import unary_union
    polygon=box(436920,4572770,436960,4572830)
    aoi={'projected':polygon.__geo_interface__,'geometry':{},'area_m2':polygon.area}
    full=tmp_path/'full.geojson';generate_contours(str(plane),str(full),interval=1)
    reference=contour_result(full,'EPSG:32617',1,aoi)
    partial=tmp_path/'partial.geojson'
    with contour_input(plane,aoi) as cropped:
        with rasterio.open(cropped) as ds:
            assert ds.width==42 and ds.height==62 and ds.crs.to_epsg()==32617
        generate_contours(str(cropped),str(partial),interval=1)
    result=contour_result(partial,'EPSG:32617',1,aoi)
    expected=unary_union([shape(f['geometry']) for f in reference['geojson']['features']])
    obtained=unary_union([shape(f['geometry']) for f in result['geojson']['features']])
    assert expected.hausdorff_distance(obtained)<1e-9


@pytest.mark.parametrize('interval',[0,-1,10001])
def test_interval_validation(interval):
    with pytest.raises(ValueError): ContourRequest(input_path='source.tif',output_name='out',interval=interval)
