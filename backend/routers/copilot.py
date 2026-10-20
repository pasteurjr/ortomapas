from fastapi import APIRouter, Depends, HTTPException
import json
import re
from backend.database.connection import get_connection
from backend.routers.auth import current_user, require_project_role

router = APIRouter()

@router.get('/copilot/memories')
async def list_memories(projeto_id: int, user: dict = Depends(current_user)):
    require_project_role(projeto_id, user, {'proprietario','editor','visualizador'})
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('SELECT id,projeto_id,chave,valor,origem,atualizado_em FROM copilot_memorias WHERE projeto_id=%s AND usuario_id=%s ORDER BY atualizado_em DESC,id DESC LIMIT 50', (projeto_id,user['id']))
        return {'memorias': [dict(row) for row in cur.fetchall()]}

@router.put('/copilot/memories')
async def save_memory(data: dict, user: dict = Depends(current_user)):
    projeto_id = data.get('projeto_id')
    key = str(data.get('chave') or '').strip().lower()
    value = data.get('valor')
    if not isinstance(projeto_id, int) or isinstance(projeto_id, bool) or projeto_id <= 0 or not re.fullmatch(r'[a-z][a-z0-9_.-]{0,79}', key):
        raise HTTPException(status_code=400, detail='projeto_id e chave valida sao obrigatorios')
    if value is None:
        raise HTTPException(status_code=400, detail='valor nao pode ser vazio')
    encoded = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    if len(encoded.encode('utf-8')) > 4096:
        raise HTTPException(status_code=413, detail='Memoria excede o limite de 4 KB')
    require_project_role(projeto_id, user, {'proprietario','editor','visualizador'})
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('INSERT INTO copilot_memorias (projeto_id,usuario_id,chave,valor,origem) VALUES (%s,%s,%s,%s::jsonb,\'usuario\') ON CONFLICT (projeto_id,usuario_id,chave) DO UPDATE SET valor=EXCLUDED.valor,origem=EXCLUDED.origem,atualizado_em=now() RETURNING id,projeto_id,chave,valor,origem,atualizado_em', (projeto_id,user['id'],key,encoded))
        row=cur.fetchone()
        cur.execute("INSERT INTO auditoria (usuario_id,acao,entidade,entidade_id,detalhes) VALUES (%s,'copilot_memory_saved','copilot_memory',%s,%s::jsonb)", (user['id'],row['id'],json.dumps({'projeto_id':projeto_id,'chave':key})))
        conn.commit()
        return dict(row)

@router.delete('/copilot/memories/{memory_id}')
async def delete_memory(memory_id: int, user: dict = Depends(current_user)):
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute('SELECT id,projeto_id,chave FROM copilot_memorias WHERE id=%s AND usuario_id=%s', (memory_id,user['id']))
        row=cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail='Memoria nao encontrada')
        require_project_role(row['projeto_id'], user, {'proprietario','editor','visualizador'})
        cur.execute('DELETE FROM copilot_memorias WHERE id=%s AND usuario_id=%s', (memory_id,user['id']))
        cur.execute("INSERT INTO auditoria (usuario_id,acao,entidade,entidade_id,detalhes) VALUES (%s,'copilot_memory_deleted','copilot_memory',%s,%s::jsonb)", (user['id'],memory_id,json.dumps({'projeto_id':row['projeto_id'],'chave':row['chave']})))
        conn.commit()
    return {'status':'ok'}

@router.get('/copilot/threads')
async def list_threads(projeto_id: int, user: dict = Depends(current_user)):
    require_project_role(projeto_id, user, {'proprietario','editor','visualizador'})
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True)
        cur.execute("SELECT id,projeto_id,usuario_id,titulo,resumo,criado_em,atualizado_em FROM copilot_threads WHERE projeto_id=%s AND usuario_id=%s ORDER BY atualizado_em DESC,id DESC", (projeto_id,user['id']))
        return {'conversas': [dict(row) for row in cur.fetchall()]}

@router.post('/copilot/threads')
async def create_thread(data: dict, user: dict = Depends(current_user)):
    projeto_id = data.get('projeto_id'); require_project_role(projeto_id, user, {'proprietario','editor','visualizador'})
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True); cur.execute("INSERT INTO copilot_threads (projeto_id, usuario_id, titulo) VALUES (%s,%s,%s) RETURNING *", (projeto_id,user['id'],data.get('titulo','Nova conversa'))); row=cur.fetchone(); conn.commit(); return dict(row)

@router.post('/copilot/threads/{thread_id}/messages')
async def add_message(thread_id: int, data: dict, user: dict = Depends(current_user)):
    if data.get('papel') not in {'user','assistant','tool'} or not data.get('conteudo'): raise HTTPException(status_code=400, detail='papel e conteudo sao obrigatorios')
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True); cur.execute("SELECT * FROM copilot_threads WHERE id=%s AND usuario_id=%s",(thread_id,user['id'])); thread=cur.fetchone()
        if not thread: raise HTTPException(status_code=404, detail='Thread nao encontrada')
        require_project_role(thread['projeto_id'], user, {'proprietario','editor','visualizador'}); ferramentas = data.get('ferramentas') or {}; cur.execute("INSERT INTO copilot_messages (thread_id,papel,conteudo,ferramentas) VALUES (%s,%s,%s,%s::jsonb) RETURNING *",(thread_id,data['papel'],data['conteudo'],json.dumps(ferramentas))); row=cur.fetchone(); cur.execute("UPDATE copilot_threads SET atualizado_em=now() WHERE id=%s", (thread_id,)); conn.commit(); return dict(row)

@router.get('/copilot/threads/{thread_id}')
async def get_thread(thread_id: int, user: dict = Depends(current_user)):
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True); cur.execute("SELECT * FROM copilot_threads WHERE id=%s AND usuario_id=%s",(thread_id,user['id'])); thread=cur.fetchone()
        if not thread: raise HTTPException(status_code=404, detail='Thread nao encontrada')
        cur.execute("SELECT * FROM copilot_messages WHERE thread_id=%s ORDER BY criado_em",(thread_id,)); thread['mensagens']=[dict(r) for r in cur.fetchall()]; return dict(thread)
