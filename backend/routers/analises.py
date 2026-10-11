"""Project-scoped analysis catalog, result files and thematic raster tiles."""
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
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
    for field,value in [('ortomapa_id',ortomapa_id),('projeto_id',projeto_id),('tipo_analise',tipo_analise),('status',status)]:
        if value is not None:
            clauses.append(f'a.{field}=%s');params.append(value)
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
        if data.get('queue_task'):
            raise HTTPException(status_code=422,detail='Fila de analise nao disponivel neste endpoint')
        if any(data.get(key) for key in ('arquivo_resultado','resultado_path','resultado_json','resultado')):
            raise HTTPException(status_code=422,detail='Resultados devem ser publicados pela ferramenta de execucao')
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
    if not row['resultado'].get('style') or not row.get('resultado_path'):
        raise HTTPException(status_code=404,detail='Analise sem raster publicado')
    scope=f'/api/analises/{analise_id}/tile/'
    return {'url':scope+'{z}/{x}/{y}.png?ticket='+media_ticket(user,scope),'expires_in':300}


@router.get('/analises/{analise_id}/tile/{z}/{x}/{y}.png')
async def tile(analise_id: int,z: int,x: int,y: int,user: dict=Depends(media_user)):
    row=analysis_for_user(analise_id,user)
    style=row['resultado'].get('style')
    if not style or not row.get('resultado_path'):
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
