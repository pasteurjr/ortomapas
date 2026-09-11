from fastapi import APIRouter, Depends, HTTPException
from backend.database.connection import get_connection
from backend.routers.auth import current_user, require_project_role

router = APIRouter()

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
        require_project_role(thread['projeto_id'], user, {'proprietario','editor','visualizador'}); cur.execute("INSERT INTO copilot_messages (thread_id,papel,conteudo,ferramentas) VALUES (%s,%s,%s,%s) RETURNING *",(thread_id,data['papel'],data['conteudo'],data.get('ferramentas',{}))); row=cur.fetchone(); conn.commit(); return dict(row)

@router.get('/copilot/threads/{thread_id}')
async def get_thread(thread_id: int, user: dict = Depends(current_user)):
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True); cur.execute("SELECT * FROM copilot_threads WHERE id=%s AND usuario_id=%s",(thread_id,user['id'])); thread=cur.fetchone()
        if not thread: raise HTTPException(status_code=404, detail='Thread nao encontrada')
        cur.execute("SELECT * FROM copilot_messages WHERE thread_id=%s ORDER BY criado_em",(thread_id,)); thread['mensagens']=[dict(r) for r in cur.fetchall()]; return dict(thread)
