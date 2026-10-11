import asyncio
import io
from contextlib import contextmanager

import numpy as np
import pytest
import rasterio
from PIL import Image
from rasterio.transform import from_bounds

from backend.utils.analysis_products import STYLES, colorize, terrain_source
from backend.utils.raster_tiles import render_analysis_tile, tile_bounds


def test_compass_palette_and_nodata():
    values=np.array([[0,45,90,135,180,225,270,315,359.]])
    rgba=colorize(values,np.ones_like(values,dtype=bool),STYLES['aspect'])
    assert rgba.shape==(1,9,4)
    assert np.array_equal(rgba[0,0],rgba[0,-1])
    assert len(np.unique(rgba[0,:,:3],axis=0))==8
    rgba=colorize(values,np.zeros_like(values,dtype=bool),STYLES['aspect'])
    assert not rgba.any()


@pytest.mark.parametrize('kind,value,expected',[('hillshade',128,[128,128,128]),('slope',30,[223,132,53]),('aspect',90,[215,198,52])])
def test_fixed_style_without_per_tile_stretch(tmp_path,kind,value,expected):
    path=tmp_path/'raster.tif'
    bounds=tile_bounds(10,500,500)
    with rasterio.open(path,'w',driver='GTiff',width=256,height=256,count=1,dtype='float32',crs='EPSG:3857',
                       transform=from_bounds(*bounds,256,256),nodata=-9999) as dst:
        values=np.full((256,256),value,dtype='float32');values[:20,:20]=-9999;dst.write(values,1)
    tile=np.asarray(Image.open(io.BytesIO(render_analysis_tile(str(path),10,500,500,STYLES[kind]))))
    assert tile.shape==(256,256,4)
    assert not tile[:20,:20].any()
    assert np.array_equal(tile[128,128],[*expected,255])


def test_source_contract_rejects_path_or_project_mismatch(monkeypatch,tmp_path):
    from fastapi import HTTPException
    from types import SimpleNamespace
    from backend.utils import analysis_products as products
    source={'id':34,'projeto_id':62,'tipo':'dsm','caminho_arquivo':str(tmp_path/'source.tif')}
    class Cursor:
        def execute(self,*args): pass
        def fetchone(self): return source
    class Conn:
        def cursor(self,**kwargs): return Cursor()
    @contextmanager
    def connection(): yield Conn()
    monkeypatch.setattr(products,'get_connection',connection)
    monkeypatch.setattr(products,'data_path',lambda p:tmp_path/p)
    token=products.tool_context.set((42,62))
    try:
        request=SimpleNamespace(ortomapa_id=34,input_path='other.tif')
        with pytest.raises(HTTPException) as error: terrain_source(request)
        assert error.value.status_code==422
        source['projeto_id']=63
        with pytest.raises(HTTPException) as error: terrain_source(request)
        assert error.value.status_code==403
    finally: products.tool_context.reset(token)


def test_analysis_routes_are_authenticated_and_scoped():
    from backend.routers.analises import router
    for route in router.routes:
        assert route.dependant.dependencies,route.path


def test_catalog_creation_cannot_inject_result(monkeypatch):
    from fastapi import HTTPException
    from backend.routers import analises
    class Cursor:
        def execute(self,*args): pass
        def fetchone(self): return {'id':34,'projeto_id':62}
    class Conn:
        def cursor(self,**kwargs): return Cursor()
    @contextmanager
    def connection(): yield Conn()
    monkeypatch.setattr(analises,'get_connection',connection)
    monkeypatch.setattr(analises,'require_project_role',lambda *args:None)
    with pytest.raises(HTTPException) as error:
        asyncio.run(analises.create_analise({'ortomapa_id':34,'tipo_analise':'terreno','resultado_path':'fake.tif'},{}))
    assert error.value.status_code==422
