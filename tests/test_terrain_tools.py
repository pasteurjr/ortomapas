import numpy as np
import pytest
import rasterio
from affine import Affine

from backend.utils.raster_metrics import terrain_aspect, terrain_gradient, terrain_illumination
from backend.tools.raster_analysis import calc_aspect
from backend.tools.gdal_tools import hillshade
from backend.tools.volumetry import cut_fill_analysis


def write(path, values, transform, crs='EPSG:32724'):
    with rasterio.open(path, 'w', driver='GTiff', width=values.shape[1], height=values.shape[0],
                       count=1, dtype='float32', crs=crs, transform=transform, nodata=-9999) as dst:
        dst.write(values.astype('float32'), 1)


@pytest.mark.parametrize('east,north,bearing', [(0,-1,0),(-1,0,90),(0,1,180),(1,0,270)])
def test_downhill_cardinal_bearings(east,north,bearing):
    assert terrain_aspect(np.array(east), np.array(north), True) == bearing


def test_flat_has_no_aspect_and_known_illumination():
    assert np.isnan(terrain_aspect(np.array(0.),np.array(0.),True))
    assert terrain_illumination(0.,0.,True,315,45) == pytest.approx(255/np.sqrt(2))
    assert terrain_illumination(-1.,0.,True,90,45) == pytest.approx(255)
    assert terrain_illumination(1.,0.,True,90,45) == pytest.approx(0,abs=1e-12)
    with pytest.raises(ValueError): terrain_illumination(0.,0.,True,315,100)


def test_rotated_feet_derivatives_and_files(tmp_path):
    grid=Affine(2,1,1000000,1,-3,200000)
    row,col=np.indices((8,8));factor=1200/3937
    dem=(100+factor*(grid.a*col+grid.b*row)).astype(float)
    source,aspect,shade=[tmp_path/name for name in ('source.tif','aspect.tif','shade.tif')]
    write(source,dem,grid,'EPSG:2263')
    calc_aspect(str(source),str(aspect));hillshade(str(source),str(shade),90,45)
    with rasterio.open(aspect) as ds: assert np.allclose(ds.read(1),270,atol=.002)
    with rasterio.open(shade) as ds: assert np.allclose(ds.read(1),0,atol=.005)


def test_aligned_cut_fill_shift_and_nodata(tmp_path):
    before,after,out=[tmp_path/name for name in ('before.tif','after.tif','diff.tif')]
    write(before,np.ones((4,4))*10,Affine(2,0,500000,0,-2,8600000))
    values=np.ones((4,4))*12;values[0,0]=-9999
    write(after,values,Affine(2,0,500002,0,-2,8600000))
    result=cut_fill_analysis(str(before),str(after),str(out))
    assert result['valid_pixels']==11
    assert result['pixel_area_m2']==4
    assert result['fill_volume_m3']==88
    assert result['cut_volume_m3']==0
    with rasterio.open(out) as ds:
        assert ds.read(1,masked=True).mask[:,0].all()
        assert np.all(ds.read(1,masked=True).compressed()==2)


def test_cut_fill_rotated_feet(tmp_path):
    before,after,out=[tmp_path/name for name in ('before.tif','after.tif','diff.tif')]
    grid=Affine(2,1,1000000,1,-3,200000)
    write(before,np.ones((4,4))*10,grid,'EPSG:2263')
    write(after,np.ones((4,4))*9,grid,'EPSG:2263')
    result=cut_fill_analysis(str(before),str(after),str(out))
    assert result['pixel_area_m2']==pytest.approx(7*(1200/3937)**2)
    assert result['cut_volume_m3']==round(16*7*(1200/3937)**2,2)


def test_cut_fill_no_overlap_or_geographic_rejected(tmp_path):
    before,after,out=[tmp_path/name for name in ('before.tif','after.tif','diff.tif')]
    write(before,np.ones((4,4)),Affine(2,0,500000,0,-2,8600000))
    write(after,np.ones((4,4)),Affine(2,0,600000,0,-2,8600000))
    with pytest.raises(ValueError,match='area comum'): cut_fill_analysis(str(before),str(after),str(out))
    write(before,np.ones((4,4)),Affine(.001,0,-38,0,-.001,-12),'EPSG:4326')
    with pytest.raises(ValueError,match='Reprojete'): cut_fill_analysis(str(before),str(after),str(out))
