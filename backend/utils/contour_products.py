"""Normalize GDAL contour lines to WGS84 GeoJSON and retain metric elevations."""
import json
import math
import tempfile
from contextlib import contextmanager
from pathlib import Path
import rasterio
from rasterio.features import geometry_window

from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform
from shapely import get_coordinates


@contextmanager
def contour_input(path, aoi):
    if aoi is None:
        yield path
        return
    with tempfile.TemporaryDirectory(prefix='ortomapas-contours-') as directory:
        cropped = str(Path(directory)/'model.tif')
        with rasterio.open(path) as source:
            window = geometry_window(source,[aoi['projected']],pad_x=1,pad_y=1)
            profile = source.profile.copy()
            profile.update(width=int(window.width),height=int(window.height),count=1,transform=source.window_transform(window))
            with rasterio.open(cropped,'w',**profile) as target:
                target.write(source.read(1,window=window),1)
        yield cropped


def contour_result(path, crs, interval, aoi=None):
    path = Path(path)
    if path.stat().st_size > 64*1024*1024:
        raise ValueError('Curvas excedem 64 MB; aumente o intervalo ou reduza os dados de entrada')
    raw = json.loads(path.read_text(encoding='utf-8'))
    to_wgs = Transformer.from_crs(crs,4326,always_xy=True).transform
    clip = shape(aoi['projected']) if aoi else None
    features = []
    vertices = 0
    for feature in raw.get('features', []):
        elevation = float(feature['properties']['elevation'])
        if not math.isfinite(elevation):
            raise ValueError('Curva com cota invalida')
        line = shape(feature['geometry'])
        if clip is not None:
            line = line.intersection(clip)
        if line.is_empty:
            continue
        lines = list(line.geoms) if line.geom_type in {'MultiLineString','GeometryCollection'} else [line]
        for part in lines:
            if part.geom_type != 'LineString' or part.length <= 0:
                continue
            geometry = mapping(transform(to_wgs,part))
            vertices += len(get_coordinates(part))
            major = math.isclose(elevation/(interval*5),round(elevation/(interval*5)),abs_tol=1e-7)
            features.append({'type':'Feature','id':len(features)+1,
                             'properties':{'elevation':elevation,'elevation_m':elevation,'major':major},'geometry':geometry})
    if not features:
        raise ValueError('Nenhuma curva neste intervalo e area; reduza o intervalo ou selecione outra area')
    if len(features)>20000 or vertices>1000000:
        raise ValueError('Curvas excedem limite de visualizacao; aumente o intervalo ou selecione uma area menor')
    collection = {'type':'FeatureCollection','features':features}
    path.write_text(json.dumps(collection),encoding='utf-8')
    from shapely.geometry import GeometryCollection
    west,south,east,north = GeometryCollection([shape(f['geometry']) for f in features]).bounds
    elevations = [f['properties']['elevation'] for f in features]
    metadata = {'geojson':collection, 'crs':'EPSG:4326', 'source_crs':str(crs),
                'bbox_oeste':west,'bbox_sul':south,'bbox_leste':east,'bbox_norte':north,
                'stats':{'feature_count':len(features),'vertex_count':vertices,'min_elevation_m':min(elevations),
                         'max_elevation_m':max(elevations),'interval_m':interval,
                         'major_count':sum(f['properties']['major'] for f in features)},
                'style':{'kind':'contours','unit':'m','legend':[{'label':'Curva','color':'#d96a19'},{'label':'Mestra','color':'#a62626'}]}}
    if aoi:
        metadata['aoi'] = {'geometry':aoi['geometry'],'crs':'EPSG:4326','area_m2':aoi['area_m2'],
                           'clip_rule':'vector intersection'}
    return metadata
