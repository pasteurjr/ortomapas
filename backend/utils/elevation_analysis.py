"""Profiles along actual lines and DSM/DTM differences on a common grid."""
import numpy as np
import rasterio
from affine import Affine
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.warp import reproject

from backend.utils.spatial_metrics import metric_geometries


def line_profile(path, geometry, crs='EPSG:4326', samples=200):
    samples = int(samples)
    if not 2 <= samples <= 1000:
        raise ValueError('Perfil precisa de 2 a 1000 amostras')
    geometries, metric_crs, inverse, factors = metric_geometries([geometry], crs)
    line = geometries[0]
    if line.geom_type != 'LineString' or line.length <= 0:
        raise ValueError('Perfil requer LineString com comprimento positivo')
    distances = np.linspace(0, line.length, samples)
    metric_points = [line.interpolate(float(d)) for d in distances]
    xs, ys = [p.x for p in metric_points], [p.y for p in metric_points]
    # Projected input expressed in feet was normalized to metres by the helper.
    if factors:
        xs = np.array(xs) / factors[0]; ys = np.array(ys) / factors[1]
    with rasterio.open(path) as ds:
        if not ds.crs:
            raise ValueError('Raster sem CRS')
        x, y = Transformer.from_crs(metric_crs, ds.crs, always_xy=True).transform(xs, ys)
        values = list(ds.sample(zip(x,y), indexes=1, masked=True))
    elevations = [None if np.ma.is_masked(v[0]) or not np.isfinite(v[0]) else float(v[0]) for v in values]
    lon, lat = Transformer.from_crs(ds.crs,4326,always_xy=True).transform(x,y)
    if not any(v is not None for v in elevations):
        raise ValueError('Linha sem amostras validas sobre o raster')
    return {'distancias_m':distances.tolist(), 'elevacoes':elevations, 'comprimento_m':float(line.length),
            'pontos':samples, 'crs_calculo':metric_crs.to_string(), 'unidade_distancia':'m',
            'unidade_elevacao':'m', 'vertical_units_assumed':True, 'metodo':'vizinho_mais_proximo',
            'geometry':geometry, 'crs_linha':crs, 'coordinates_wgs84':list(map(list,zip(lon,lat)))}


def aligned_difference(dsm_path, dtm_path, max_size=128):
    with rasterio.open(dsm_path) as dsm, rasterio.open(dtm_path) as dtm:
        if not dsm.crs or not dtm.crs:
            raise ValueError('DSM e DTM precisam de CRS')
        scale = min(1, max_size / max(dsm.width,dsm.height))
        width, height = max(1,round(dsm.width*scale)), max(1,round(dsm.height*scale))
        affine = dsm.transform * Affine.scale(dsm.width/width,dsm.height/height)
        a = dsm.read(1,out_shape=(height,width),masked=True,resampling=Resampling.bilinear).astype(float).filled(np.nan)
        b = np.full((height,width),np.nan,dtype=float)
        source = dtm.read(1,masked=True).astype(float).filled(np.nan)
        reproject(source,b,src_transform=dtm.transform,src_crs=dtm.crs,src_nodata=np.nan,
                  dst_transform=affine,dst_crs=dsm.crs,dst_nodata=np.nan,resampling=Resampling.bilinear)
        diff = a-b
        valid = diff[np.isfinite(diff)]
        if not valid.size:
            raise ValueError('DSM e DTM sem area comum valida')
        return {'width':width,'height':height,'min':float(valid.min()),'max':float(valid.max()),
                'mean':float(valid.mean()),'bounds':list(dsm.bounds),'crs':str(dsm.crs),
                'units':'m','vertical_units_assumed':True,'valid_pixels':int(valid.size),
                'alignment':'DTM reprojected to sampled DSM grid',
                'differences':[[float(v) if np.isfinite(v) else None for v in row] for row in diff]}
