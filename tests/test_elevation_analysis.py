import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from backend.utils.elevation_analysis import line_profile, aligned_difference


def write(path,values,transform,crs='EPSG:32617'):
    with rasterio.open(path,'w',driver='GTiff',width=values.shape[1],height=values.shape[0],count=1,dtype='float32',crs=crs,transform=transform,nodata=-9999) as ds:
        ds.write(values.astype('float32'),1)


def test_profile_follows_line_not_column_average(tmp_path):
    source=tmp_path/'plane.tif'
    row,col=np.indices((10,10));write(source,100+col*2+row*3,from_origin(500000,4500000,2,2))
    line={'type':'LineString','coordinates':[[500001,4499999],[500019,4499999]]}
    result=line_profile(source,line,'EPSG:32617',10)
    assert result['comprimento_m']==18
    assert result['elevacoes']==list(range(100,120,2))
    assert result['distancias_m']==list(range(0,20,2))


def test_profile_nodata_is_gap(tmp_path):
    path=tmp_path/'holes.tif';values=np.ones((3,5))*20;values[1,2]=-9999
    write(path,values,from_origin(500000,4500000,1,1))
    result=line_profile(path,{'type':'LineString','coordinates':[[500000.5,4499998.5],[500004.5,4499998.5]]},'EPSG:32617',5)
    assert result['elevacoes']==[20,20,None,20,20]


def test_difference_realigns_shifted_grids(tmp_path):
    a,b=tmp_path/'dsm.tif',tmp_path/'dtm.tif'
    write(a,np.full((6,6),12.),from_origin(500000,4500000,1,1))
    write(b,np.full((6,6),10.),from_origin(500002,4500000,1,1))
    result=aligned_difference(a,b)
    assert result['min']==result['max']==result['mean']==2
    assert result['valid_pixels']==24
    assert all(row[:2]==[None,None] for row in result['differences'])


def test_difference_no_overlap_rejected(tmp_path):
    a,b=tmp_path/'a.tif',tmp_path/'b.tif'
    write(a,np.ones((3,3)),from_origin(500000,4500000,1,1))
    write(b,np.ones((3,3)),from_origin(600000,4500000,1,1))
    with pytest.raises(ValueError,match='area comum'):aligned_difference(a,b)


def test_profile_feet_distance_is_metric(tmp_path):
    path=tmp_path/'feet.tif'
    write(path,np.ones((10,10))*100,from_origin(1000000,200000,10,10),'EPSG:2263')
    result=line_profile(path,{'type':'LineString','coordinates':[[1000005,199995],[1000095,199995]]},'EPSG:2263',10)
    assert result['comprimento_m']==pytest.approx(90*(1200/3937))
    assert result['elevacoes']==[100]*10


def test_difference_different_crs(tmp_path):
    from pyproj import Transformer
    from rasterio.transform import from_bounds
    a,b=tmp_path/'utm.tif',tmp_path/'wgs84.tif'
    write(a,np.full((6,6),12.),from_origin(500000,4500000,1,1))
    transform=Transformer.from_crs(32617,4326,always_xy=True)
    left,bottom=transform.transform(500000,4499994);right,top=transform.transform(500006,4500000)
    write(b,np.full((6,6),10.),from_bounds(left,bottom,right,top,6,6),'EPSG:4326')
    result=aligned_difference(a,b)
    assert result['mean']==pytest.approx(2)
    assert result['valid_pixels']>=25
