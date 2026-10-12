import numpy as np
import pytest
import rasterio
from affine import Affine
from pyproj import Transformer
from shapely.geometry import box, mapping, Polygon
from shapely.ops import transform

from backend.tools.volumetry import calc_volume
from backend.utils.terrain_aoi import prepare_aoi
from backend.utils.analysis_products import colorize, STYLES
from backend.routers.tools import VolumeRequest


def raster(path, values, grid=Affine(1,0,500000,0,-1,4600000), crs='EPSG:32617'):
    with rasterio.open(path,'w',driver='GTiff',width=values.shape[1],height=values.shape[0],
                       count=1,dtype='float32',crs=crs,transform=grid,nodata=-9999) as ds:
        ds.write(values.astype('float32'),1)
    return path


def area(path, polygon):
    geom=transform(Transformer.from_crs(32617,4326,always_xy=True).transform,polygon)
    return prepare_aoi(str(path),mapping(geom))


def test_prism_40000_excludes_outside_values(tmp_path):
    values=np.full((220,120),999.,dtype='float32');values[10:210,10:110]=102
    src=raster(tmp_path/'model.tif',values)
    aoi=area(src,box(500010,4599790,500110,4599990))
    output=tmp_path/'delta.tif'
    result=calc_volume(str(src),100.,str(output),aoi)
    assert result['volume_above_m3']==40000
    assert result['volume_below_m3']==0
    assert result['valid_pixels']==20000
    assert result['valid_area_m2']==pytest.approx(20000)
    with rasterio.open(output) as ds:
        assert np.all(ds.read(1,masked=True).compressed()==2)
        assert ds.width<120 and ds.height<220


def test_hole_nodata_and_both_signs(tmp_path):
    values=np.array([[102,98,102,98],[102,-9999,102,98],[102,98,102,98],[102,98,102,98]],dtype=float)
    src=raster(tmp_path/'model.tif',values)
    polygon=Polygon(box(500000,4599996,500004,4600000).exterior.coords,
                    [box(500002,4599997,500003,4599998).exterior.coords])
    aoi=area(src,polygon)
    result=calc_volume(str(src),100,str(tmp_path/'delta.tif'),aoi)
    assert result['valid_pixels']==14
    assert result['volume_above_m3']==14
    assert result['volume_below_m3']==14
    assert result['net_volume_m3']==0
    assert result['cut_area_m2']==7 and result['fill_area_m2']==7


def test_delta_minus9999_is_valid_not_nodata(tmp_path):
    src=raster(tmp_path/'model.tif',np.ones((2,2)))
    out=tmp_path/'delta.tif'
    calc_volume(str(src),10000,str(out))
    with rasterio.open(out) as ds:
        values=ds.read(1,masked=True)
        assert not np.ma.getmaskarray(values).any()
        assert np.all(values==-9999)


def test_rotated_pixel_area_and_feet(tmp_path):
    src=raster(tmp_path/'model.tif',np.full((2,2),102.),Affine(10,2,1000000,3,-10,200000),'EPSG:2263')
    result=calc_volume(str(src),100)
    assert result['pixel_area_m2']==pytest.approx(106*(1200/3937)**2)
    assert result['volume_above_m3']==round(8*106*(1200/3937)**2,2)


def test_volume_colors_sign_and_transparency():
    style={**STYLES['volume'],'min':-2,'max':2}
    rgba=colorize(np.array([[-2.,0,2]]),np.array([[True,False,True]]),style)
    assert np.array_equal(rgba[0,0],[33,102,172,255])
    assert np.array_equal(rgba[0,1],[0,0,0,0])
    assert np.array_equal(rgba[0,2],[178,24,43,255])
    assert np.array_equal(colorize(np.array([[0.]]),np.ones((1,1),bool),style)[0,0],[247,247,247,255])


@pytest.mark.parametrize('value',[float('nan'),float('inf'),float('-inf')])
def test_request_rejects_nonfinite_reference(value,tmp_path):
    with pytest.raises(ValueError): VolumeRequest(dsm_path='model.tif',reference_elevation=value)
    src=raster(tmp_path/'model.tif',np.ones((2,2)))
    with pytest.raises(ValueError,match='finita'):
        calc_volume(str(src),value)


def test_empty_area_rejected(tmp_path):
    src=raster(tmp_path/'empty.tif',np.full((4,4),-9999.))
    aoi=area(src,box(500000,4599996,500004,4600000))
    with pytest.raises(ValueError,match='sem pixels validos'):
        calc_volume(str(src),100,None,aoi)


def test_explicit_source_requires_editor_even_without_output_name(monkeypatch):
    import asyncio
    from fastapi import HTTPException
    from backend.utils import resource_access as access
    class Request:
        url=type('URL',(),{'path':'/api/tools/volume'})()
        async def json(self):
            return {'dsm_path':'model.tif','ortomapa_id':34,'projeto_id':62,'reference_elevation':100}
    monkeypatch.setattr(access,'file_projects',lambda *args:{62})
    def deny(*args): raise HTTPException(status_code=403,detail='Apenas leitura')
    monkeypatch.setattr(access,'require_project_role',deny)
    with pytest.raises(HTTPException) as error:
        asyncio.run(access.authorize_tools(Request(),{'id':1}))
    assert error.value.status_code==403
