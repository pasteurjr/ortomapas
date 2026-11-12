import json

import numpy as np
import pytest
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


def test_priority_flood_increment_survives_float32_at_realistic_elevation(tmp_path):
    source=tmp_path/'high_pit.tif';output=tmp_path/'high_filled.tif'
    dem=np.full((7,7),300,dtype='float32');dem[3,3]=250
    write_dem(source,dem);hydrology.fill_sinks(str(source),str(output))
    with rasterio.open(output) as ds:
        result=ds.read(1);tags=ds.tags()
    assert result[3,3]>300
    assert float(tags['epsilon'])>=float(np.spacing(np.float32(300)))*2


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


def test_d8_routes_submillimeter_flat_to_lower_edge(tmp_path):
    dem_path=tmp_path/'flat.tif';direction=tmp_path/'direction.tif';accumulation=tmp_path/'acc.tif'
    dem=np.full((9,9),300,dtype='float32')
    dem[-1,:]=299.99
    write_dem(dem_path,dem)
    hydrology.flow_direction(str(dem_path),str(direction))
    hydrology.flow_accumulation(str(direction),str(accumulation))
    with rasterio.open(direction) as ds:
        fdir=ds.read(1);tags=ds.tags()
    with rasterio.open(accumulation) as ds:
        acc=ds.read(1)
    # The flat plateau must route through a downhill seed instead of keeping
    # most cells directionless; flow accumulation must remain acyclic.
    assert np.all(fdir[:-1,:] != 0)
    assert np.all(fdir[-1,:] == 0)
    assert int(acc[-1,:].sum()) >= dem.size-9
    assert int(tags['near_flat_cells_resolved']) >= 1
    assert float(tags['flat_tolerance_m']) >= float(np.spacing(np.float32(300)))*8


def test_d8_never_routes_into_nodata(tmp_path):
    dem_path=tmp_path/'nodata_wall.tif';direction=tmp_path/'direction.tif'
    dem=np.tile(np.array([5,4,3,2,1],dtype='float32'),(5,1))
    dem[:,3]=-9999
    write_dem(dem_path,dem)
    hydrology.flow_direction(str(dem_path),str(direction))
    with rasterio.open(direction) as ds:
        fdir=ds.read(1)
    assert np.all(fdir[:,3] == 0)
    # Cells next to the NoData wall must not see its sentinel value as a very
    # low elevation and drain horizontally into it.
    assert np.all(fdir[:,2] != 1)


def test_hydrography_connector_conditions_dem_and_reports_effect(tmp_path):
    dem_path=tmp_path/'dem.tif';line_path=tmp_path/'connector.geojson';output=tmp_path/'conditioned.tif'
    write_dem(dem_path,np.full((9,9),100,dtype='float32'))
    line_path.write_text(json.dumps({
        'type':'FeatureCollection',
        'crs':{'type':'name','properties':{'name':'EPSG:3857'}},
        'features':[{'type':'Feature','properties':{'id':'connector'},
                     'geometry':{'type':'LineString','coordinates':[[4.5,8.5],[4.5,0.5]]}}],
    }))
    result=hydrology.condition_dem_with_hydrography(str(dem_path),str(line_path),str(output),0.05)
    with rasterio.open(dem_path) as original,rasterio.open(output) as conditioned:
        before=original.read(1);after=conditioned.read(1);tags=conditioned.tags()
    assert result['features_used']==1
    assert result['cells_conditioned']>0
    assert np.all(after<=before)
    assert float(tags['burn_depth_m'])==0.05
    assert float(after[:,4].min())<100


def test_snap_stream_lines_and_metric_threshold(tmp_path):
    direction=tmp_path/'direction.tif';accumulation=tmp_path/'acc.tif';network=tmp_path/'network.geojson'
    fdir=np.zeros((6,4),dtype='int16');fdir[:-1]=4
    acc=np.repeat(np.arange(1,7,dtype='int32')[:,None],4,axis=1)
    for path,values,dtype in ((direction,fdir,'int16'),(accumulation,acc,'int32')):
        with rasterio.open(path,'w',driver='GTiff',width=4,height=6,count=1,dtype=dtype,crs='EPSG:3857',transform=from_origin(0,6,1,1),nodata=0) as dst: dst.write(values,1)
    snapped=hydrology.snap_pour_point(str(accumulation),1.5,4.5,5)
    assert snapped['row']==5 and snapped['accumulation_cells']==6
    assert snapped['snap_distance_m']<=5
    result=hydrology.extract_stream_lines(str(accumulation),str(direction),str(network),3)
    data=json.loads(network.read_text())
    assert result['threshold_cells']==3 and result['total_length_m']==12
    assert result['feature_count']==4 and len(data['features'])==4
    assert all(feature['geometry']['type']=='LineString' for feature in data['features'])


def test_stream_lines_filter_by_strahler_order(tmp_path):
    direction=tmp_path/'branch_direction.tif';accumulation=tmp_path/'branch_acc.tif'
    order_one=tmp_path/'order_one.geojson';order_two=tmp_path/'order_two.geojson'
    fdir=np.zeros((5,5),dtype='int16')
    fdir[1,1]=2   # tributary A flows SE
    fdir[1,3]=8   # tributary B flows SW
    fdir[2,2]=4   # confluence flows south
    fdir[3,2]=4
    acc=np.full((5,5),100,dtype='int32')
    for path,values,dtype in ((direction,fdir,'int16'),(accumulation,acc,'int32')):
        with rasterio.open(path,'w',driver='GTiff',width=5,height=5,count=1,dtype=dtype,
                           crs='EPSG:3857',transform=from_origin(0,5,1,1),nodata=0) as dst:
            dst.write(values,1)
    all_orders=hydrology.extract_stream_lines(str(accumulation),str(direction),str(order_one),1)
    order_two_result=hydrology.extract_stream_lines(str(accumulation),str(direction),str(order_two),1,2)
    assert all_orders['maximum_strahler_order']==2
    assert order_two_result['candidate_cells']==25
    assert order_two_result['stream_cells']==3
    assert order_two_result['minimum_strahler_order']==2
    assert abs(order_two_result['total_length_m']-2)<1e-9
    all_features=json.loads(order_one.read_text())['features']
    assert {feature['properties']['ordem_strahler'] for feature in all_features}=={1,2}
    assert set(order_two_result['order_lengths_m'])=={'2'}
    with pytest.raises(ValueError,match='Strahler'):
        hydrology.extract_stream_lines(str(accumulation),str(direction),str(order_two),1,13)


def test_snap_radius_uses_pixel_center_distance_for_anisotropic_grid(tmp_path):
    accumulation=tmp_path/'anisotropic_acc.tif'
    values=np.ones((4,4),dtype='int32');values[1,2]=99
    with rasterio.open(accumulation,'w',driver='GTiff',width=4,height=4,count=1,dtype='int32',
                       crs='EPSG:3857',transform=from_origin(0,6,4,1),nodata=0) as dst:
        dst.write(values,1)
    # The high-accumulation neighbor is 4 m away. The old sqrt(pixel-area)
    # approximation measured it as 2 m and incorrectly accepted it at radius 3.
    snapped=hydrology.snap_pour_point(str(accumulation),6,4.5,3)
    assert (snapped['row'],snapped['col'])==(1,1)
    assert snapped['snap_distance_m']<=3


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


def test_direction_and_accumulation_products_are_routable_and_styled(tmp_path):
    dem=tmp_path/'east_falling_dem.tif';direction=tmp_path/'direction.tif';accumulation=tmp_path/'accumulation.tif'
    values=np.tile(np.arange(6,0,-1,dtype='float32'),(5,1))
    write_dem(dem,values)
    hydrology.flow_direction(str(dem),str(direction))
    hydrology.flow_accumulation(str(direction),str(accumulation))
    with rasterio.open(direction) as ds:
        flow=ds.read(1)
        assert ds.nodata==0
        assert np.all(flow[:,:-1]==1)  # ESRI D8 value 1 points east.
    with rasterio.open(accumulation) as ds:
        accumulated=ds.read(1)
        assert np.array_equal(accumulated[2],np.arange(1,7,dtype='int32'))
        assert ds.crs.to_epsg()==3857

    direction_rgba=colorize(np.array([[1.,2.,4.,8.,16.,32.,64.,128.]]),
        np.ones((1,8),dtype=bool),STYLES['flow_direction'])
    assert len({tuple(pixel) for pixel in direction_rgba[0]})==8
    accum_style={**STYLES['flow_accumulation'],'min':1,'max':6}
    accumulation_rgba=colorize(np.array([[1.,6.]]),np.ones((1,2),dtype=bool),accum_style)
    assert np.array_equal(accumulation_rgba[0,0],[254,243,199,255])
    assert np.array_equal(accumulation_rgba[0,1],[29,78,216,255])
