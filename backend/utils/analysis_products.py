"""Persistent, project-scoped terrain outputs and their fixed display contracts."""
from pathlib import Path
import numpy as np
import rasterio
from rasterio.warp import transform_bounds
from psycopg2.extras import Json
from fastapi import HTTPException

from backend.database.connection import get_connection
from backend.utils.resource_access import data_path, tool_context

ASPECT_COLORS = ['#dc4545','#df8435','#d7c634','#4caa66','#30aaa8','#4085d1','#7352b9','#be589f']
STYLES = {
    'aspect': {'unit':'graus','method':'nearest','kind':'aspect','min':0,'max':360,
               'legend':[{'label':label,'color':color} for label,color in zip(['N','NE','E','SE','S','SO','O','NO'],ASPECT_COLORS)]},
    'hillshade': {'unit':'intensidade','method':'bilinear','kind':'hillshade','min':0,'max':255,
                  'legend':[{'label':'0','color':'#000000'},{'label':'255','color':'#ffffff'}]},
    'slope': {'unit':'graus','method':'bilinear','kind':'slope','min':0,'max':90,
              'legend':[{'label':str(value),'color':color} for value,color in zip([0,10,30,60,90],['#26764a','#d7c634','#df8435','#dc4545','#7352b9'])]},
}
NAMES = {'aspect':'Orientacao do relevo','hillshade':'Sombreamento','slope':'Declividade'}


def terrain_source(request):
    """Resolve the explicit source before generating files; old callers stay file-only."""
    if request.ortomapa_id is None:
        return None
    context = tool_context.get()
    if not context:
        raise HTTPException(status_code=403, detail='Contexto de projeto necessario')
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM ortomapas WHERE id=%s',(request.ortomapa_id,))
        source=cur.fetchone()
    if not source:
        raise HTTPException(status_code=404, detail='Modelo de origem nao encontrado')
    if source['projeto_id'] != context[1]:
        raise HTTPException(status_code=403, detail='Modelo pertence a outro projeto')
    if str(source['tipo']).lower() not in {'dsm','dtm'}:
        raise HTTPException(status_code=422, detail='Selecione um DSM ou DTM')
    if data_path(source['caminho_arquivo']) != data_path(request.input_path):
        raise HTTPException(status_code=422, detail='Arquivo difere do modelo selecionado')
    return source


def publish_terrain(source, operation, output, statistics, parameters, aoi=None):
    path=data_path(output)
    with rasterio.open(path) as ds:
        west,south,east,north=transform_bounds(ds.crs,4326,*ds.bounds)
        metadata={'crs':str(ds.crs),'width':ds.width,'height':ds.height,
                  'bbox_oeste':west,'bbox_sul':south,'bbox_leste':east,'bbox_norte':north,
                  'style':STYLES[operation],'stats':statistics['band_1'],
                  'provenance':{'source_ortomapa_id':source['id'],'source_path':source['caminho_arquivo'],
                                'operation':operation,'vertical_units_assumed':'m','scope':'full raster',
                                'algorithm':'metric finite differences','created_by':tool_context.get()[0]}}
        if aoi:
            metadata['aoi'] = {'geometry':aoi['geometry'], 'crs':'EPSG:4326',
                               'area_m2':aoi['area_m2'], 'pixel_area_m2':aoi['pixel_area_m2'],
                               'valid_area_m2':statistics['band_1']['valid_pixels']*aoi['pixel_area_m2'],
                               'mask_rule':'pixel center', 'derivative_context':'original raster neighborhood'}
            metadata['provenance']['scope'] = 'aoi'
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('''INSERT INTO analises (ortomapa_id,projeto_id,tipo_analise,nome,parametros,
            resultado_path,resultado_json,status,data_analise) VALUES (%s,%s,%s,%s,%s,%s,%s,'concluida',now()) RETURNING *''',
            (source['id'],source['projeto_id'],'terreno',NAMES[operation]+(' - area selecionada' if aoi else ''),Json(parameters),str(path),Json(metadata)))
        row=dict(cur.fetchone());conn.commit()
    return serialize_analysis(row)


def serialize_analysis(row):
    row=dict(row)
    row['resultado']=row.get('resultado_json') or {}
    return row


def publish_contours(source, output, metadata, parameters):
    metadata['provenance'] = {'source_ortomapa_id':source['id'], 'source_path':source['caminho_arquivo'],
                              'operation':'contours','vertical_units_assumed':'m',
                              'scope':'aoi' if metadata.get('aoi') else 'full raster',
                              'algorithm':'GDAL contour + vector intersection','created_by':tool_context.get()[0]}
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute('''INSERT INTO analises (ortomapa_id,projeto_id,tipo_analise,nome,parametros,
            resultado_path,resultado_json,status,data_analise) VALUES (%s,%s,%s,%s,%s,%s,%s,'concluida',now()) RETURNING *''',
            (source['id'],source['projeto_id'],'terreno','Curvas de nivel'+(' - area selecionada' if metadata.get('aoi') else ''),
             Json(parameters),str(data_path(output)),Json(metadata)))
        row=dict(cur.fetchone());conn.commit()
    return serialize_analysis(row)


def colorize(values, valid, style):
    values=np.nan_to_num(values)
    if style['kind']=='aspect':
        palette=np.array([[int(color[i:i+2],16) for i in (1,3,5)] for color in ASPECT_COLORS],dtype=np.uint8)
        rgb=palette[(np.floor((values+22.5)/45).astype(int)%8)]
    elif style['kind']=='hillshade':
        rgb=np.repeat(np.clip(values,0,255).astype(np.uint8)[...,None],3,axis=-1)
    else:
        palette=np.array([[int(item['color'][i:i+2],16) for i in (1,3,5)] for item in STYLES['slope']['legend']])
        rgb=np.stack([np.interp(values,[0,10,30,60,90],palette[:,i]) for i in range(3)],axis=-1).astype(np.uint8)
    rgba=np.dstack([rgb,valid.astype(np.uint8)*255]);rgba[~valid,:3]=0
    return rgba
