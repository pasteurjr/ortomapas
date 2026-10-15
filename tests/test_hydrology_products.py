import json

import numpy as np
import rasterio
from rasterio.transform import from_origin

from backend.tools import hydrology
from backend.utils.analysis_products import STYLES, colorize


def write_dem(path,values,nodata=-9999):
    with rasterio.open(path,'w',driver='GTiff',width=values.shape[1],height=values.shape[0],count=1,
                       dtype='float32',crs='EPSG:3857',transform=from_origin(0,values.shape[0],1,1),nodata=nodata) as dst:
        dst.write(values.astype('float32'),1)


def test_priority_flood_fills_closed_depression(tmp_path):
    source=tmp_path/'pit.tif';output=tmp_path/'filled.tif'
    dem=np.full((7,7),10,dtype='float32');dem[3,3]=1
    write_dem(source,dem);hydrology.fill_sinks(str(source),str(output))
    with rasterio.open(output) as ds:
        result=ds.read(1);tags=ds.tags()
    assert result[3,3]>10
    assert int(tags['raised_cells'])>=1
    assert np.allclose(result[[0,-1]],10)


def test_d8_plane_accumulation_and_watershed(tmp_path):
    dem_path=tmp_path/'plane.tif';direction=tmp_path/'direction.tif';accumulation=tmp_path/'acc.tif';basin=tmp_path/'basin.tif'
    dem=100-np.arange(6,dtype='float32')[:,None]+np.zeros((6,4),dtype='float32')
    write_dem(dem_path,dem);hydrology.flow_direction(str(dem_path),str(direction));hydrology.flow_accumulation(str(direction),str(accumulation))
    with rasterio.open(direction) as ds: fdir=ds.read(1)
    with rasterio.open(accumulation) as ds: acc=ds.read(1)
    assert np.all(fdir[:-1]==4) and np.all(fdir[-1]==0)
    assert np.array_equal(acc[:,1],np.arange(1,7))
    result=hydrology.watershed_from_flow(str(direction),str(basin),5,1)
    with rasterio.open(basin) as ds: mask=ds.read(1)
    assert result['watershed_cells']==6
    assert np.array_equal(mask[:,1],np.ones(6))
    assert mask.sum()==6


def test_snap_stream_lines_and_metric_threshold(tmp_path):
    direction=tmp_path/'direction.tif';accumulation=tmp_path/'acc.tif';network=tmp_path/'network.geojson'
    fdir=np.zeros((6,4),dtype='int16');fdir[:-1]=4
    acc=np.repeat(np.arange(1,7,dtype='int32')[:,None],4,axis=1)
    for path,values,dtype in ((direction,fdir,'int16'),(accumulation,acc,'int32')):
        with rasterio.open(path,'w',driver='GTiff',width=4,height=6,count=1,dtype=dtype,crs='EPSG:3857',transform=from_origin(0,6,1,1),nodata=0) as dst: dst.write(values,1)
    snapped=hydrology.snap_pour_point(str(accumulation),1.5,4.5,5)
    assert snapped['row']==5 and snapped['accumulation_cells']==6
    result=hydrology.extract_stream_lines(str(accumulation),str(direction),str(network),3)
    data=json.loads(network.read_text())
    assert result['threshold_cells']==3 and result['total_length_m']==12
    assert result['feature_count']==4 and len(data['features'])==4
    assert all(feature['geometry']['type']=='LineString' for feature in data['features'])


def test_working_grid_twi_and_styles(tmp_path):
    source=tmp_path/'large.tif';work=tmp_path/'work.tif';slope=tmp_path/'slope.tif';acc=tmp_path/'acc.tif';twi=tmp_path/'twi.tif'
    values=100-np.arange(256,dtype='float32')[:,None]*.1+np.zeros((256,128),dtype='float32')
    write_dem(source,values);grid=hydrology.prepare_dem(str(source),str(work),128)
    assert grid['working_shape']==[128,64] and grid['pixel_area_m2']==4
    with rasterio.open(work) as ds:
        profile=ds.profile;shape=(ds.height,ds.width)
    write_dem(slope,np.full(shape,5,dtype='float32'))
    with rasterio.open(acc,'w',**{**profile,'dtype':'int32','nodata':0}) as dst: dst.write(np.full(shape,10,dtype='int32'),1)
    hydrology.calc_twi(str(slope),str(acc),str(twi))
    with rasterio.open(twi) as ds: result=ds.read(1,masked=True).compressed()
    assert result.size==shape[0]*shape[1] and np.isfinite(result).all()
    watershed=colorize(np.array([[1.,np.nan]]),np.array([[True,False]]),STYLES['watershed'])
    assert np.array_equal(watershed[0,0],[37,99,235,255]) and not watershed[0,1].any()
    style={**STYLES['twi'],'min':0,'max':20}
    colored=colorize(np.array([[0.,10.,20.]]),np.ones((1,3),dtype=bool),style)
    assert np.array_equal(colored[0,0],[180,83,9,255])
    assert np.array_equal(colored[0,2],[3,105,161,255])
