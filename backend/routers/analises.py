"""Project-scoped analysis catalog, result files and thematic raster tiles."""
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from psycopg2.extras import Json

from backend.database.connection import get_connection
from backend.routers.auth import current_user, require_project_role
from backend.utils.resource_access import READ_ROLES, data_path, file_projects, media_user, media_ticket
from backend.utils.analysis_products import serialize_analysis
from backend.utils.raster_tiles import render_analysis_tile, tile_bounds

router=APIRouter()


def analysis_for_user(analysis_id,user,roles=READ_ROLES):
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM analises WHERE id=%s',(analysis_id,))
        row=cur.fetchone()
    if not row:
        raise HTTPException(status_code=404,detail='Analise nao encontrada')
    require_project_role(row['projeto_id'],user,roles)
    return serialize_analysis(row)


@router.get('/analises')
async def list_analises(ortomapa_id: int | None=Query(None), projeto_id: int | None=Query(None),
                        tipo_analise: str | None=Query(None), status: str | None=Query(None),
                        user: dict=Depends(current_user)):
    if projeto_id is not None:
        require_project_role(projeto_id,user,READ_ROLES)
    clauses=[];params=[]
    if user['perfil']!='admin':
        clauses.append("EXISTS (SELECT 1 FROM projeto_usuarios pu WHERE pu.projeto_id=a.projeto_id AND pu.usuario_id=%s AND pu.papel IN ('proprietario','editor','visualizador'))")
        params.append(user['id'])
    for field,value in [('ortomapa_id',ortomapa_id),('projeto_id',projeto_id),('tipo_analise',tipo_analise)]:
        if value is not None:
            clauses.append(f'a.{field}=%s');params.append(value)
    if status is not None:
        statuses=[item.strip() for item in status.split(',') if item.strip()]
        if statuses:
            clauses.append('a.status IN ('+','.join(['%s']*len(statuses))+')')
            params.extend(statuses)
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('SELECT a.* FROM analises a'+(' WHERE '+' AND '.join(clauses) if clauses else '')+' ORDER BY a.criado_em DESC',params)
        rows=[serialize_analysis(row) for row in cur.fetchall()]
    return {'total':len(rows),'analises':rows}


@router.get('/analises/{analise_id}')
async def get_analise(analise_id: int,user: dict=Depends(current_user)):
    return analysis_for_user(analise_id,user)


@router.post('/analises',status_code=201)
async def create_analise(data: dict,user: dict=Depends(current_user)):
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('SELECT * FROM ortomapas WHERE id=%s',(data.get('ortomapa_id'),))
        source=cur.fetchone()
        if not source:
            raise HTTPException(status_code=404,detail='Ortomapa nao encontrado')
        require_project_role(source['projeto_id'],user,{'proprietario','editor'})
        if data.get('projeto_id') not in {None,source['projeto_id']}:
            raise HTTPException(status_code=422,detail='Projeto difere do ortomapa')
        if not data.get('tipo_analise'):
            raise HTTPException(status_code=422,detail='Tipo de analise necessario')
        if any(data.get(key) for key in ('arquivo_resultado','resultado_path','resultado_json','resultado')):
            raise HTTPException(status_code=422,detail='Resultados devem ser publicados pela ferramenta de execucao')
        if data.get('queue_task'):
            try:
                parameters=data.get('parametros') or {}
                if isinstance(parameters,str):
                    import json
                    parameters=json.loads(parameters)
                if not isinstance(parameters,dict):
                    raise ValueError('parametros deve ser um objeto')
                analysis_type=data['tipo_analise']
                if analysis_type=='classificacao_solo':
                    algorithm=str(parameters.get('algorithm','kmeans')).lower()
                    n_clusters=int(parameters.get('n_clusters',parameters.get('n_classes',5)))
                    if algorithm!='kmeans':
                        raise ValueError('A fila aceita somente K-Means para classificacao')
                    if not 2 <= n_clusters <= 12:
                        raise ValueError('O numero de classes deve estar entre 2 e 12')
                    parameters={**parameters,'algorithm':'kmeans','n_clusters':n_clusters}
                    agent_name='agente_classificacao'
                elif analysis_type=='indice_vegetacao':
                    index_name=str(parameters.get('index_name','VARI')).upper()
                    if index_name not in {'VARI','TGI','EXG','GLI'}:
                        raise ValueError('Indice RGB deve ser VARI, TGI, ExG ou GLI')
                    parameters={**parameters,'index_name':index_name}
                    agent_name='agente_analise_raster'
                elif analysis_type=='terreno':
                    terrain_type=str(parameters.get('terrain_type','slope')).lower()
                    if terrain_type not in {'slope','aspect','hillshade','contours'}:
                        raise ValueError('A fila de terreno aceita declividade, orientacao, hillshade ou curvas de nivel')
                    parameters={**parameters,'terrain_type':terrain_type}
                    if terrain_type=='contours':
                        import math
                        interval=float(parameters.get('interval',5.0))
                        if not math.isfinite(interval) or not 0 < interval <= 10000:
                            raise ValueError('O intervalo de curvas deve estar entre 0 e 10000 metros')
                        parameters['interval']=interval
                    if terrain_type=='hillshade':
                        import math
                        azimuth=float(parameters.get('azimuth',315))
                        altitude=float(parameters.get('altitude',45))
                        if not math.isfinite(azimuth) or not 0 <= azimuth <= 360:
                            raise ValueError('Azimute deve estar entre 0 e 360 graus')
                        if not math.isfinite(altitude) or not 0 <= altitude <= 90:
                            raise ValueError('Elevacao solar deve estar entre 0 e 90 graus')
                        parameters.update(azimuth=azimuth,altitude=altitude)
                    agent_name='agente_analise_terreno'
                elif analysis_type=='hidrologia':
                    hydro_type=str(parameters.get('hydro_type','')).lower()
                    import math
                    if hydro_type in {'flow_direction','flow_accumulation','twi'}:
                        parameters={**parameters,'hydro_type':hydro_type}
                    elif hydro_type=='drainage':
                        minimum_area=float(parameters.get('minimum_area_m2',1000))
                        if not math.isfinite(minimum_area) or not 1 <= minimum_area <= 1_000_000_000:
                            raise ValueError('A area contribuinte minima deve estar entre 1 e 1000000000 m²')
                        parameters={**parameters,'hydro_type':hydro_type,'minimum_area_m2':minimum_area}
                    elif hydro_type=='watershed':
                        outlet=parameters.get('outlet')
                        if not isinstance(outlet,dict):
                            raise ValueError('Selecione um exutorio no mapa antes de enfileirar a bacia')
                        lat=float(outlet.get('lat',float('nan')));lon=float(outlet.get('lng',outlet.get('lon',float('nan'))))
                        radius=float(parameters.get('snap_radius_m',5))
                        if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:
                            raise ValueError('Exutorio deve conter latitude/longitude WGS84 validas')
                        if not math.isfinite(radius) or not 0<=radius<=1000:
                            raise ValueError('Raio de ajuste do exutorio deve estar entre 0 e 1000 metros')
                        parameters={**parameters,'hydro_type':hydro_type,'outlet':{'lat':lat,'lon':lon},'snap_radius_m':radius}
                    else:
                        raise ValueError('A fila hidrologica aceita direcao/acumulacao D8, TWI, rede ou bacia')
                    agent_name='agente_analise_hidrologia'
                else:
                    raise ValueError('A fila aceita K-Means RGB, indices de vegetacao, derivadas de terreno, rede D8 ou bacia hidrologica')
            except (TypeError,ValueError) as exc:
                raise HTTPException(status_code=422,detail=str(exc))

            from backend.utils.resource_access import data_path
            import rasterio
            source_type=str(source.get('tipo','')).lower()
            is_terrain=analysis_type in {'terreno','hidrologia'}
            if is_terrain and source_type not in {'dsm','dtm'}:
                raise HTTPException(status_code=422,detail='Analises de terreno e hidrologia exigem um DSM ou DTM')
            if not is_terrain and source_type not in {'ortomosaico','rgb','multispectral'}:
                raise HTTPException(status_code=422,detail='A analise RGB exige um ortomosaico')
            try:
                source_path=data_path(source['caminho_arquivo'])
                with rasterio.open(source_path) as raster:
                    if is_terrain and raster.count < 1:
                        raise HTTPException(status_code=422,detail='O modelo de elevacao nao contem banda de dados')
                    if not is_terrain and raster.count < 3:
                        raise HTTPException(status_code=422,detail='O ortomosaico precisa ter pelo menos tres bandas RGB')
                    if analysis_type=='classificacao_solo' and (raster.crs is None or not raster.crs.is_projected):
                        raise HTTPException(status_code=422,detail='K-Means exige raster RGB em CRS projetado para calcular areas; reprojete o ortomosaico primeiro')
                    if is_terrain and (raster.crs is None or not raster.crs.is_projected):
                        raise HTTPException(status_code=422,detail='Analise de terreno/hidrologia exige DSM/DTM em CRS projetado com unidades horizontais metricas')
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(status_code=422,detail=f'Nao foi possivel validar o raster RGB: {exc}')

            task_parameters={**parameters,'_project_id':source['projeto_id'],'_user_id':user['id']}
            default_name=('Classificacao de solo K-Means' if analysis_type=='classificacao_solo'
                          else f'Indice de vegetacao {parameters["index_name"]}' if analysis_type=='indice_vegetacao'
                    else f'Analise de terreno {parameters["terrain_type"]}' if analysis_type=='terreno'
                          else {'drainage':'Rede de drenagem potencial D8','watershed':'Bacia contribuinte D8',
                                'flow_direction':'Direcao de fluxo D8','flow_accumulation':'Acumulacao de fluxo D8',
                                'twi':'Indice topografico de umidade (TWI)'}[parameters['hydro_type']])
            cur.execute('''INSERT INTO analises
                (ortomapa_id,projeto_id,tipo_analise,nome,parametros,agente_ia,status,observacoes)
                VALUES (%s,%s,%s,%s,%s,%s,'em_fila',%s) RETURNING *''',
                (source['id'],source['projeto_id'],data['tipo_analise'],
                 data.get('nome') or default_name,Json(parameters),
                 agent_name,'Aguardando processamento em fila.'))
            analysis=cur.fetchone()
            task_parameters['_analysis_id']=analysis['id']
            cur.execute('''INSERT INTO tarefas_agentes
                (ortomapa_id,tipo_tarefa,agente,prioridade,parametros,status)
                VALUES (%s,%s,%s,%s,%s,'pendente') RETURNING id''',
                (source['id'],analysis_type,agent_name,5,Json(task_parameters)))
            task_id=cur.fetchone()['id']
            cur.execute('''INSERT INTO auditoria (usuario_id,acao,entidade,entidade_id,detalhes)
                VALUES (%s,%s,%s,%s,%s)''',
                (user['id'],'analise_enfileirada','analise',analysis['id'],Json({'tarefa_id':task_id,'agente':agent_name})))
            conn.commit()
            return JSONResponse(status_code=202,content=jsonable_encoder({**serialize_analysis(analysis),'tarefa_id':task_id}))
        cur.execute('''INSERT INTO analises (ortomapa_id,projeto_id,tipo_analise,nome,parametros,status,observacoes)
            VALUES (%s,%s,%s,%s,%s,'pendente',%s) RETURNING *''',
            (source['id'],source['projeto_id'],data['tipo_analise'],data.get('nome') or data['tipo_analise'],Json(data.get('parametros') or {}),data.get('observacoes')))
        row=cur.fetchone();conn.commit()
    return serialize_analysis(row)


@router.get('/analises/{analise_id}/resultado')
async def get_analise_resultado(analise_id: int,user: dict=Depends(media_user)):
    row=analysis_for_user(analise_id,user)
    if not row.get('resultado_path'):
        raise HTTPException(status_code=404,detail='Analise sem arquivo de resultado')
    path=data_path(row['resultado_path'])
    file_projects(str(path),user)
    if not path.is_file():
        raise HTTPException(status_code=404,detail='Arquivo de resultado nao encontrado')
    return FileResponse(path,filename=path.name,headers={'Cache-Control':'private, no-store'})


@router.get('/analises/{analise_id}/download-access')
async def download_access(analise_id: int,user: dict=Depends(current_user)):
    row=analysis_for_user(analise_id,user)
    if not row.get('resultado_path') or not data_path(row['resultado_path']).is_file():
        raise HTTPException(status_code=404,detail='Arquivo de resultado nao encontrado')
    scope=f'/api/analises/{analise_id}/resultado'
    return {'url':scope+'?ticket='+media_ticket(user,scope),'expires_in':300}


@router.get('/analises/{analise_id}/tile-access')
async def tile_access(analise_id: int,user: dict=Depends(current_user)):
    row=analysis_for_user(analise_id,user)
    if row['resultado'].get('geojson') or not row['resultado'].get('style') or not row.get('resultado_path'):
        raise HTTPException(status_code=404,detail='Analise sem raster publicado')
    scope=f'/api/analises/{analise_id}/tile/'
    return {'url':scope+'{z}/{x}/{y}.png?ticket='+media_ticket(user,scope),'expires_in':300}


@router.get('/analises/{analise_id}/tile/{z}/{x}/{y}.png')
def tile(analise_id: int,z: int,x: int,y: int,user: dict=Depends(media_user)):
    row=analysis_for_user(analise_id,user)
    style=row['resultado'].get('style')
    if row['resultado'].get('geojson') or not style or not row.get('resultado_path'):
        raise HTTPException(status_code=404,detail='Analise sem raster publicado')
    path=data_path(row['resultado_path']);file_projects(str(path),user)
    if not path.is_file():
        raise HTTPException(status_code=404,detail='Raster nao encontrado')
    try:
        tile_bounds(z,x,y)
        png=render_analysis_tile(str(path),z,x,y,style)
    except ValueError as exc:
        raise HTTPException(status_code=422,detail=str(exc))
    return StreamingResponse(io.BytesIO(png),media_type='image/png',headers={'Cache-Control':'private, no-store'})


@router.delete('/analises/{analise_id}')
async def delete_analise(analise_id: int,user: dict=Depends(current_user)):
    row=analysis_for_user(analise_id,user,{'proprietario','editor'})
    # Another recorded analysis may reference a file; retention is separate.
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('DELETE FROM analises WHERE id=%s',(analise_id,));conn.commit()
    return {'message':'Analise removida do catalogo; arquivo preservado','id':row['id']}
