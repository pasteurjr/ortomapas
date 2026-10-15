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
    'volume': {'unit':'m (modelo - referencia)','method':'nearest','kind':'volume','min':-1,'max':1,
               'legend':[{'label':'Aterro','color':'#2166ac'},{'label':'0','color':'#f7f7f7'},{'label':'Corte','color':'#b2182b'}]},
    'elevation_change': {'unit':'m (depois - antes)','method':'nearest','kind':'elevation_change','min':-1,'max':1,
                         'legend':[{'label':'Remocao','color':'#b2182b'},{'label':'Estavel','color':'#f7f7f7'},
                                   {'label':'Deposicao','color':'#2166ac'}]},
    'vegetation': {'unit':'indice RGB','method':'bilinear','kind':'vegetation','min':-1,'max':1,
                   'legend':[{'label':'Baixo','color':'#8c510a'},{'label':'Medio','color':'#f6e8c3'},
                             {'label':'Alto','color':'#1b7837'}]},
    'classification': {'unit':'grupo espectral','method':'nearest','kind':'classification','min':1,'max':7,
                       'colors':['#3b82f6','#f59e0b','#22c55e','#ef4444','#8b5cf6','#06b6d4',
                                 '#eab308','#ec4899','#64748b','#14b8a6','#f97316','#84cc16']},
}
NAMES = {'aspect':'Orientacao do relevo','hillshade':'Sombreamento','slope':'Declividade','volume':'Corte/aterro por cota'}


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


def image_source(request, path_value):
    """Resolve an RGB-capable source while retaining file-only legacy calls."""
    if request.ortomapa_id is None:
        return None
    context=tool_context.get()
    if not context or request.projeto_id != context[1]:
        raise HTTPException(status_code=403,detail='Contexto do projeto invalido')
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True);cur.execute('SELECT * FROM ortomapas WHERE id=%s',(request.ortomapa_id,));source=cur.fetchone()
    if not source:
        raise HTTPException(status_code=404,detail='Ortomapa de origem nao encontrado')
    if source['projeto_id'] != context[1]:
        raise HTTPException(status_code=403,detail='Ortomapa pertence a outro projeto')
    if str(source['tipo']).lower() not in {'ortomosaico','rgb','multispectral'}:
        raise HTTPException(status_code=422,detail='Selecione um ortomosaico RGB ou multiespectral')
    if data_path(source['caminho_arquivo']) != data_path(path_value):
        raise HTTPException(status_code=422,detail='Arquivo difere do ortomapa selecionado')
    return source


def _raster_percentiles(path):
    with rasterio.open(path) as ds:
        sample=ds.read(1,out_shape=(min(ds.height,512),min(ds.width,512)),masked=True).compressed()
    sample=sample[np.isfinite(sample)]
    if not sample.size:
        raise ValueError('Resultado sem pixels validos')
    low,high=np.percentile(sample,[2,98])
    if high <= low:
        low,high=float(sample.min()),float(sample.max())
    if high <= low:
        low,high=low-.01,high+.01
    return float(low),float(high)


def publish_image_analysis(source, operation, output, statistics, parameters, aoi=None, details=None):
    """Publish visible-band indices and unsupervised RGB groups."""
    path=data_path(output);details=details or {}
    if operation=='vegetation':
        low,high=_raster_percentiles(path);middle=(low+high)/2
        index=parameters['index_name'].upper()
        style={**STYLES['vegetation'],'min':low,'max':high,'legend':[
            {'label':f'{low:.3f} Baixo','color':'#8c510a'},
            {'label':f'{middle:.3f}','color':'#f6e8c3'},
            {'label':f'{high:.3f} Alto','color':'#1b7837'}]}
        name=f'Indice RGB {index}';kind='vegetacao'
        result_stats=statistics['band_1']
    else:
        colors=STYLES['classification']['colors'][:details['n_clusters']]
        style={**STYLES['classification'],'max':details['n_clusters'],'colors':colors,'legend':[
            {'label':f"Grupo {cluster['cluster']} · RGB {','.join(map(str,cluster['center_rgb']))}",'color':colors[i]}
            for i,cluster in enumerate(details['clusters'])]}
        name=f"Grupos espectrais KMeans ({details['n_clusters']})";kind='classificacao'
        result_stats={key:details[key] for key in ('n_clusters','total_valid_pixels','sample_pixels','pixel_area_m2','valid_area_m2')}
    with rasterio.open(path) as ds:
        west,south,east,north=transform_bounds(ds.crs,4326,*ds.bounds)
        metadata={'crs':str(ds.crs),'width':ds.width,'height':ds.height,
                  'bbox_oeste':west,'bbox_sul':south,'bbox_leste':east,'bbox_norte':north,
                  'style':style,'stats':result_stats,
                  'provenance':{'source_ortomapa_id':source['id'],'source_path':source['caminho_arquivo'],
                                'operation':parameters.get('index_name',operation),'bands':'R=1,G=2,B=3',
                                'scope':'aoi' if aoi else 'full raster','created_by':tool_context.get()[0]}}
        if operation=='classification':
            metadata['classes']=[{'nome':f"Grupo {cluster['cluster']}",'area':cluster['area_m2'],
                                  'percentual':cluster['percent'],'pixel_count':cluster['pixel_count'],
                                  'center_rgb':cluster['center_rgb'],'color':style['colors'][i]}
                                 for i,cluster in enumerate(details['clusters'])]
            metadata['provenance'].update(algorithm='KMeans RGB normalizado',semantic_labels=False,
                                          training_sample_pixels=details['sample_pixels'])
        else:
            metadata['provenance'].update(algorithm='visible-band index',nir_used=False)
        if aoi:
            valid_area=(details.get('valid_area_m2') if operation=='classification'
                        else statistics['band_1']['valid_pixels']*aoi['pixel_area_m2'])
            metadata['aoi']={'geometry':aoi['geometry'],'crs':'EPSG:4326','area_m2':aoi['area_m2'],
                             'pixel_area_m2':aoi['pixel_area_m2'],'valid_area_m2':valid_area,
                             'mask_rule':'pixel center'}
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('''INSERT INTO analises (ortomapa_id,projeto_id,tipo_analise,nome,parametros,
            resultado_path,resultado_json,status,data_analise) VALUES (%s,%s,%s,%s,%s,%s,%s,'concluida',now()) RETURNING *''',
            (source['id'],source['projeto_id'],kind,name+(' - area selecionada' if aoi else ''),
             Json(parameters),str(path),Json(metadata)))
        row=dict(cur.fetchone());conn.commit()
    return serialize_analysis(row)


def comparison_sources(request):
    """Resolve and validate the ordered pair used in a temporal elevation comparison."""
    if request.ortomapa_antes_id == request.ortomapa_depois_id:
        raise HTTPException(status_code=422, detail='Selecione dois modelos distintos')
    context = tool_context.get()
    if not context or request.projeto_id != context[1]:
        raise HTTPException(status_code=403, detail='Contexto do projeto invalido')
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM ortomapas WHERE id IN (%s,%s)',
                    (request.ortomapa_antes_id,request.ortomapa_depois_id))
        rows={row['id']:row for row in cur.fetchall()}
    before=rows.get(request.ortomapa_antes_id);after=rows.get(request.ortomapa_depois_id)
    if not before or not after:
        raise HTTPException(status_code=404, detail='Modelo anterior ou posterior nao encontrado')
    if before['projeto_id'] != context[1] or after['projeto_id'] != context[1]:
        raise HTTPException(status_code=403, detail='Os modelos devem pertencer ao projeto ativo')
    if str(before['tipo']).lower() not in {'dsm','dtm'} or str(after['tipo']).lower() not in {'dsm','dtm'}:
        raise HTTPException(status_code=422, detail='Selecione apenas DSM ou DTM')
    if str(before['tipo']).lower() != str(after['tipo']).lower():
        raise HTTPException(status_code=422, detail='Compare modelos do mesmo tipo: DSM com DSM ou DTM com DTM')
    if data_path(before['caminho_arquivo']) != data_path(request.dsm1_path) or data_path(after['caminho_arquivo']) != data_path(request.dsm2_path):
        raise HTTPException(status_code=422, detail='Arquivos diferem dos modelos selecionados')
    return before,after


def publish_elevation_change(before, after, output, statistics, parameters, aoi=None):
    """Publish a temporal terrain difference and its catalog record atomically."""
    path=data_path(output)
    threshold=parameters['threshold']
    low=min(statistics['band_1']['min'],-threshold,-0.01)
    high=max(statistics['band_1']['max'],threshold,0.01)
    style={**STYLES['elevation_change'],'min':low,'max':high,'threshold':threshold,'legend':[
        {'label':f'{low:.2f} m Remocao','color':'#b2182b'},
        {'label':f'Estavel +/- {threshold:.2f} m (transparente)','color':'#d1d5db'},
        {'label':f'+{high:.2f} m Deposicao','color':'#2166ac'}]}
    with rasterio.open(path) as ds:
        west,south,east,north=transform_bounds(ds.crs,4326,*ds.bounds)
        metadata={'crs':str(ds.crs),'width':ds.width,'height':ds.height,
                  'bbox_oeste':west,'bbox_sul':south,'bbox_leste':east,'bbox_norte':north,
                  'style':style,'stats':statistics['band_1'],
                  'provenance':{'source_before_id':before['id'],'source_after_id':after['id'],
                                'source_before_path':before['caminho_arquivo'],'source_after_path':after['caminho_arquivo'],
                                'operation':'after - before','alignment':'after reprojected to before grid',
                                'vertical_units_assumed':'m','scope':'aoi' if aoi else 'common valid area',
                                'sign_convention':'positive=deposition/fill; negative=removal/cut; net=fill-cut',
                                'created_by':tool_context.get()[0]}}
        if aoi:
            metadata['aoi']={'geometry':aoi['geometry'],'crs':'EPSG:4326','area_m2':aoi['area_m2'],
                             'pixel_area_m2':aoi['pixel_area_m2'],
                             'valid_area_m2':statistics['band_1']['valid_area_m2'],'mask_rule':'pixel center'}
    before_date=before.get('data_processamento') or before.get('criado_em')
    after_date=after.get('data_processamento') or after.get('criado_em')
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('''INSERT INTO analises (ortomapa_id,projeto_id,tipo_analise,nome,parametros,
            resultado_path,resultado_json,status,data_analise) VALUES (%s,%s,'mudancas',%s,%s,%s,%s,'concluida',now()) RETURNING *''',
            (after['id'],after['projeto_id'],'Mudanca de elevacao'+(' - area selecionada' if aoi else ''),
             Json(parameters),str(path),Json(metadata)))
        analysis=dict(cur.fetchone())
        cur.execute('''INSERT INTO comparacoes_temporais (projeto_id,ortomapa_antes_id,ortomapa_depois_id,
            data_antes,data_depois,tipo_comparacao,resultado_path,estatisticas,observacoes)
            VALUES (%s,%s,%s,COALESCE(%s,now()),COALESCE(%s,now()),'elevacao',%s,%s,%s) RETURNING id''',
            (after['projeto_id'],before['id'],after['id'],before_date,after_date,str(path),Json(metadata['stats']),
             'Diferenca depois - antes; positivo indica deposicao, negativo indica remocao'))
        comparison_id=cur.fetchone()['id'];conn.commit()
    return serialize_analysis(analysis),comparison_id


def publish_terrain(source, operation, output, statistics, parameters, aoi=None):
    path=data_path(output)
    style=STYLES[operation]
    if operation=='volume':
        low=min(statistics['band_1']['min'],-0.01)
        high=max(statistics['band_1']['max'],0.01)
        style={**style,'min':low,'max':high,'legend':[
            {'label':f'{low:.2f} Aterro','color':'#2166ac'}, {'label':'0','color':'#f7f7f7'},
            {'label':f'+{high:.2f} Corte','color':'#b2182b'}]}
    with rasterio.open(path) as ds:
        west,south,east,north=transform_bounds(ds.crs,4326,*ds.bounds)
        metadata={'crs':str(ds.crs),'width':ds.width,'height':ds.height,
                  'bbox_oeste':west,'bbox_sul':south,'bbox_leste':east,'bbox_norte':north,
                  'style':style,'stats':statistics['band_1'],
                  'provenance':{'source_ortomapa_id':source['id'],'source_path':source['caminho_arquivo'],
                                'operation':operation,'vertical_units_assumed':'m','scope':'full raster',
                                'algorithm':'model - reference' if operation=='volume' else 'metric finite differences','created_by':tool_context.get()[0]}}
        if operation=='volume':
            metadata['provenance'].update(reference_elevation_m=parameters['reference_elevation'],
                                          sign_convention='positive=cut; negative=fill; net=cut-fill')
        if aoi:
            metadata['aoi'] = {'geometry':aoi['geometry'], 'crs':'EPSG:4326',
                               'area_m2':aoi['area_m2'], 'pixel_area_m2':aoi['pixel_area_m2'],
                               'valid_area_m2':statistics['band_1']['valid_pixels']*aoi['pixel_area_m2'],
                               'mask_rule':'pixel center', 'derivative_context':'not applicable' if operation=='volume' else 'original raster neighborhood'}
            metadata['provenance']['scope'] = 'aoi'
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('''INSERT INTO analises (ortomapa_id,projeto_id,tipo_analise,nome,parametros,
            resultado_path,resultado_json,status,data_analise) VALUES (%s,%s,%s,%s,%s,%s,%s,'concluida',now()) RETURNING *''',
            (source['id'],source['projeto_id'],'volume' if operation=='volume' else 'terreno',NAMES[operation]+(' - area selecionada' if aoi else ''),Json(parameters),str(path),Json(metadata)))
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
    elif style['kind']=='elevation_change':
        threshold=style.get('threshold',0)
        palette=np.array([[178,24,43],[247,247,247],[247,247,247],[33,102,172]])
        stops=[style['min'],-threshold,threshold,style['max']]
        rgb=np.stack([np.interp(values,stops,palette[:,i]) for i in range(3)],axis=-1).astype(np.uint8)
    elif style['kind']=='volume':
        palette=np.array([[33,102,172],[247,247,247],[178,24,43]])
        rgb=np.stack([np.interp(values,[style['min'],0,style['max']],palette[:,i]) for i in range(3)],axis=-1).astype(np.uint8)
    elif style['kind']=='vegetation':
        palette=np.array([[140,81,10],[246,232,195],[27,120,55]])
        middle=(style['min']+style['max'])/2
        rgb=np.stack([np.interp(values,[style['min'],middle,style['max']],palette[:,i]) for i in range(3)],axis=-1).astype(np.uint8)
    elif style['kind']=='classification':
        palette=np.array([[int(color[i:i+2],16) for i in (1,3,5)] for color in style['colors']],dtype=np.uint8)
        indexes=np.clip(np.rint(values).astype(int)-1,0,len(palette)-1)
        rgb=palette[indexes]
    else:
        palette=np.array([[int(item['color'][i:i+2],16) for i in (1,3,5)] for item in STYLES['slope']['legend']])
        rgb=np.stack([np.interp(values,[0,10,30,60,90],palette[:,i]) for i in range(3)],axis=-1).astype(np.uint8)
    rgba=np.dstack([rgb,valid.astype(np.uint8)*255]);rgba[~valid,:3]=0
    if style['kind']=='elevation_change':
        rgba[valid & (np.abs(values) <= style.get('threshold',0)),3]=0
    return rgba
