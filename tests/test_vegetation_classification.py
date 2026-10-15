import numpy as np
import pytest
import rasterio
from pydantic import ValidationError
from rasterio.transform import from_origin
from shapely.geometry import box, mapping

from backend.routers.tools import ClassifyRequest, SegmentRequest
from backend.tools.raster_analysis import calc_vegetation_index
from backend.tools.segmentation import segment_ortomapa
from backend.utils.analysis_products import STYLES, colorize


def write_rgb(path, bands, *, crs='EPSG:3857', nodata=None):
    bands=np.asarray(bands)
    with rasterio.open(path,'w',driver='GTiff',width=bands.shape[2],height=bands.shape[1],count=3,
                       dtype=bands.dtype,crs=crs,transform=from_origin(0,bands.shape[1],1,1),nodata=nodata) as dst:
        dst.write(bands)


@pytest.mark.parametrize('index,expected',[
    ('VARI',(80-40)/(80+40-20)),
    ('TGI',80-.39*40-.61*20),
    ('ExG',2*80-40-20),
    ('GLI',(2*80-40-20)/(2*80+40+20)),
])
def test_visible_indices_match_formula_and_preserve_mask(tmp_path,index,expected):
    source=tmp_path/'rgb.tif';output=tmp_path/f'{index}.tif'
    values=np.zeros((3,4,4),dtype='uint8')
    values[0]=40;values[1]=80;values[2]=20
    values[:,0,0]=255
    write_rgb(source,values,nodata=255)
    calc_vegetation_index(str(source),str(output),index)
    with rasterio.open(output) as ds:
        result=ds.read(1,masked=True)
        assert result.mask[0,0]
        assert np.allclose(result.compressed(),expected,rtol=0,atol=1e-5)
        assert ds.tags()['bands']=='R=1,G=2,B=3'


def test_visible_index_crops_and_masks_to_aoi(tmp_path):
    source=tmp_path/'rgb.tif';output=tmp_path/'aoi.tif'
    values=np.stack([np.full((10,10),40),np.full((10,10),80),np.full((10,10),20)]).astype('uint8')
    write_rgb(source,values)
    polygon=mapping(box(2,5,6,9))
    calc_vegetation_index(str(source),str(output),'VARI',{'projected':polygon})
    with rasterio.open(output) as ds:
        assert (ds.width,ds.height)==(4,4)
        assert ds.bounds==rasterio.coords.BoundingBox(2,5,6,9)
        assert ds.read(1,masked=True).count()==16
        assert ds.tags()['analysis_scope']=='aoi'


def test_kmeans_known_colors_is_deterministic_and_keeps_valid_black(tmp_path):
    source=tmp_path/'colors.tif';first=tmp_path/'groups1.tif';second=tmp_path/'groups2.tif'
    image=np.zeros((3,12,12),dtype='uint8')
    image[:,:,:4]=np.array([0,0,0])[:,None,None]
    image[:,:,4:8]=np.array([20,210,30])[:,None,None]
    image[:,:,8:]=np.array([220,30,20])[:,None,None]
    write_rgb(source,image)
    one=segment_ortomapa(str(source),str(first),3)
    two=segment_ortomapa(str(source),str(second),3)
    with rasterio.open(first) as a,rasterio.open(second) as b:
        labels=a.read(1)
        assert np.array_equal(labels,b.read(1))
        assert set(np.unique(labels))=={1,2,3}
        assert labels[0,0] != 0
    assert one['total_valid_pixels']==144
    assert one['clusters']==two['clusters']
    assert sum(item['pixel_count'] for item in one['clusters'])==144
    assert sum(item['percent'] for item in one['clusters'])==pytest.approx(100,abs=1e-3)
    assert sorted(item['pixel_count'] for item in one['clusters'])==[48,48,48]
    assert one['valid_area_m2']==pytest.approx(144)


def test_kmeans_aoi_excludes_outside_colors(tmp_path):
    source=tmp_path/'colors.tif';output=tmp_path/'groups.tif'
    image=np.zeros((3,8,12),dtype='uint8')
    image[:,:,:4]=np.array([10,10,10])[:,None,None]
    image[:,:,4:8]=np.array([20,210,30])[:,None,None]
    image[:,:,8:]=np.array([220,30,20])[:,None,None]
    write_rgb(source,image)
    aoi={'projected':mapping(box(0,0,8,8))}
    result=segment_ortomapa(str(source),str(output),2,aoi=aoi)
    with rasterio.open(output) as ds:
        assert (ds.width,ds.height)==(8,8)
        assert set(np.unique(ds.read(1)))=={1,2}
    assert result['total_valid_pixels']==64


def test_classification_limits_and_insufficient_pixels(tmp_path):
    with pytest.raises(ValidationError):
        ClassifyRequest(ortomapa_path='x.tif',n_clusters=1)
    with pytest.raises(ValidationError):
        ClassifyRequest(ortomapa_path='x.tif',n_clusters=13)
    with pytest.raises(ValidationError):
        SegmentRequest(input_path='x.tif',output_name='x',n_clusters=1)
    source=tmp_path/'tiny.tif';output=tmp_path/'groups.tif'
    write_rgb(source,np.ones((3,1,1),dtype='uint8'))
    with pytest.raises(ValueError,match='insuficientes'):
        segment_ortomapa(str(source),str(output),2)


def test_vegetation_and_classification_color_contracts():
    vegetation={**STYLES['vegetation'],'min':-1,'max':1}
    rgba=colorize(np.array([[-1.,0.,1.,np.nan]]),np.array([[True,True,True,False]]),vegetation)
    assert np.array_equal(rgba[0,0],[140,81,10,255])
    assert np.array_equal(rgba[0,1],[246,232,195,255])
    assert np.array_equal(rgba[0,2],[27,120,55,255])
    assert not rgba[0,3].any()
    classification={**STYLES['classification'],'colors':STYLES['classification']['colors'][:3]}
    groups=colorize(np.array([[1,2,3,0]]),np.array([[True,True,True,False]]),classification)
    assert np.array_equal(groups[0,0],[59,130,246,255])
    assert np.array_equal(groups[0,1],[245,158,11,255])
    assert np.array_equal(groups[0,2],[34,197,94,255])
    assert not groups[0,3].any()
