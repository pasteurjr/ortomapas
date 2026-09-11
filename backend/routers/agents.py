from fastapi import APIRouter, Depends, HTTPException
from backend.agents.llm_client import LMStudioClient
from backend.routers.auth import current_user, require_project_role
from backend.agents.schemas import TOOL_CATALOG
from backend.database.connection import get_connection
from backend.config import DATA_DIR
from pathlib import Path
import rasterio, laspy
import numpy as np
from backend.agents.llm_client import LMStudioClient

router = APIRouter()

@router.post('/agents/ask')
async def ask_copilot(data: dict, user: dict = Depends(current_user)):
    prompt = (data.get('prompt') or '').strip()
    if not prompt: raise HTTPException(status_code=400, detail='Prompt obrigatorio')
    context = data.get('context') or {}; project_id = context.get('projeto_id')
    if project_id:
        require_project_role(project_id, user, {'proprietario','editor','visualizador'})
        with get_connection() as conn:
            cur=conn.cursor(dictionary=True); cur.execute("SELECT id,nome,status FROM projetos WHERE id=%s",(project_id,)); project=cur.fetchone(); cur.execute("SELECT id,data_voo,drone,camera,status,num_fotos FROM voos WHERE projeto_id=%s ORDER BY data_voo DESC NULLS LAST",(project_id,)); voos=[dict(r) for r in cur.fetchall()]; cur.execute("SELECT p.id,p.tipo,p.formato,p.crs FROM produtos_processamento p JOIN processamentos_odm j ON j.id=p.processamento_id WHERE j.projeto_id=%s ORDER BY p.id",(project_id,)); produtos=[dict(r) for r in cur.fetchall()]; cur.execute("SELECT id,tipo,categoria,rotulo,centro_lat,centro_lon FROM anotacoes a JOIN ortomapas o ON o.id=a.ortomapa_id WHERE o.projeto_id=%s ORDER BY a.id DESC LIMIT 50",(project_id,)); anotacoes=[dict(r) for r in cur.fetchall()]; context={**context,'projeto':dict(project) if project else None,'voos':voos,'produtos_autorizados':produtos,'anotacoes_recentes':anotacoes}
    messages = [{'role':'system','content':'Voce e o Ortomapas Copilot. Responda em JSON conforme o schema. Nunca invente dados; solicite ferramentas quando precisar de dados do projeto.'}, {'role':'user','content': f'Contexto autorizado: {context}\nPergunta: {prompt}'}]
    try:
        client = LMStudioClient(); result, telemetry = client.complete(messages, TOOL_CATALOG); tool_results = []
        for call in result.tool_calls:
            try: tool_results.append({'tool': call.name, 'result': await execute_tool({'name': call.name, 'arguments': call.arguments}, user)})
            except HTTPException as exc: tool_results.append({'tool': call.name, 'error': exc.detail})
        if tool_results:
            messages.extend([{'role':'assistant','content':result.model_dump_json()}, {'role':'user','content':f'Resultados das ferramentas: {tool_results}. Responda ao usuario com base nesses dados.'}]); final, final_telemetry = client.complete(messages, [])
            return {'status':'ok','resposta':final.model_dump(),'ferramentas_executadas':tool_results,'telemetria':{**telemetry,'final':final_telemetry}}
        return {'status':'ok','resposta':result.model_dump(),'telemetria':telemetry}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f'Falha no LM Studio: {exc}')

@router.get('/agents/tools')
async def agent_tools(user: dict = Depends(current_user)):
    return {'tools': [tool.model_dump() for tool in TOOL_CATALOG], 'count': len(TOOL_CATALOG)}

@router.post('/agents/tools/execute')
async def execute_tool(data: dict, user: dict = Depends(current_user)):
    name = data.get('name'); args = data.get('arguments') or {}; project_id = args.get('projeto_id')
    if name not in {tool.name for tool in TOOL_CATALOG}: raise HTTPException(status_code=400, detail='Ferramenta nao permitida')
    if name == 'listar_produtos':
        require_project_role(project_id, user, {'proprietario','editor','visualizador'})
        with get_connection() as conn:
            cur=conn.cursor(dictionary=True); cur.execute("SELECT p.*, j.projeto_id FROM produtos_processamento p JOIN processamentos_odm j ON j.id=p.processamento_id WHERE j.projeto_id=%s ORDER BY p.id",(project_id,)); return {'status':'ok','dados':[dict(r) for r in cur.fetchall()]}
    if name in {'calcular_declividade','calcular_aspecto','gerar_hillshade'}:
        product_id=args.get('produto_id')
        with get_connection() as conn:
            cur=conn.cursor(dictionary=True); cur.execute("SELECT p.*, j.projeto_id FROM produtos_processamento p JOIN processamentos_odm j ON j.id=p.processamento_id WHERE p.id=%s AND p.tipo IN ('dsm','dtm')",(product_id,)); product=cur.fetchone()
        if not product: raise HTTPException(status_code=404, detail='DSM/DTM nao encontrado')
        require_project_role(product['projeto_id'], user, {'proprietario','editor','visualizador'})
        with rasterio.open(Path(DATA_DIR)/product['caminho']) as ds: arr=ds.read(1, out_shape=(min(512,ds.height),min(512,ds.width)), resampling=rasterio.enums.Resampling.bilinear).astype(float); px=abs(ds.transform.a); py=abs(ds.transform.e)
        gy,gx=np.gradient(arr,py,px)
        if name == 'calcular_declividade': values=np.degrees(np.arctan(np.hypot(gx,gy)))
        elif name == 'calcular_aspecto': values=(np.degrees(np.arctan2(-gx,gy))+360)%360
        else: values=(np.maximum(0, np.cos(np.radians(45))*np.cos(np.arctan(np.hypot(gx,gy))) + np.sin(np.radians(45))*np.sin(np.arctan(np.hypot(gx,gy)))*np.cos(np.radians(315)-np.arctan2(gy,gx))))*255
        return {'status':'ok','dados':{'produto_id':product_id,'operacao':name,'min':float(values.min()),'max':float(values.max()),'media':float(values.mean()),'grade':list(values.shape)}}
    if name == 'comparar_dsm_dtm':
        processing_id=args.get('processamento_id')
        with get_connection() as conn:
            cur=conn.cursor(dictionary=True); cur.execute("SELECT * FROM processamentos_odm WHERE id=%s",(processing_id,)); job=cur.fetchone(); cur.execute("SELECT * FROM produtos_processamento WHERE processamento_id=%s AND tipo IN ('dsm','dtm')",(processing_id,)); products={r['tipo']:r for r in cur.fetchall()}
        if not job or len(products)<2: raise HTTPException(status_code=404, detail='DSM e DTM nao encontrados')
        require_project_role(job['projeto_id'], user, {'proprietario','editor','visualizador'})
        with rasterio.open(Path(DATA_DIR)/products['dsm']['caminho']) as dsm, rasterio.open(Path(DATA_DIR)/products['dtm']['caminho']) as dtm:
            a=dsm.read(1,out_shape=(64,64),resampling=rasterio.enums.Resampling.bilinear); b=dtm.read(1,out_shape=(64,64),resampling=rasterio.enums.Resampling.bilinear); diff=np.asarray(a-b,dtype=float)
        return {'status':'ok','dados':{'processamento_id':processing_id,'min':float(diff.min()),'max':float(diff.max()),'media':float(diff.mean()),'grade':[64,64]}}
    product_id = args.get('produto_id')
    with get_connection() as conn:
        cur=conn.cursor(dictionary=True); cur.execute("SELECT p.*, j.projeto_id FROM produtos_processamento p JOIN processamentos_odm j ON j.id=p.processamento_id WHERE p.id=%s",(product_id,)); product=cur.fetchone()
    if not product: raise HTTPException(status_code=404, detail='Produto nao encontrado')
    require_project_role(product['projeto_id'], user, {'proprietario','editor','visualizador'}); path=Path(DATA_DIR)/product['caminho']
    if name == 'estatisticas_laz':
        with laspy.open(path) as reader: h=reader.header; return {'status':'ok','dados':{'produto_id':product_id,'pontos':h.point_count,'crs':str(h.parse_crs()) if h.parse_crs() else None,'min':list(h.mins),'max':list(h.maxs)}}
    with rasterio.open(path) as ds:
        arr=ds.read(masked=True); return {'status':'ok','dados':{'produto_id':product_id,'largura':ds.width,'altura':ds.height,'bandas':ds.count,'crs':str(ds.crs) if ds.crs else None,'resolucao':[abs(ds.transform.a),abs(ds.transform.e)],'min':float(arr.min()),'max':float(arr.max()),'media':float(arr.mean()),'nodata':float(arr.mask.mean()) if hasattr(arr.mask,'mean') else 0}}

@router.get('/agents/status')
async def agent_status(user: dict = Depends(current_user)):
    client = LMStudioClient()
    try:
        models = client.models(); available = [m.get('id') for m in models.get('data', [])]
        return {'online': True, 'base_url': client.base_url, 'configured_model': client.model, 'available_models': available}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'LM Studio indisponivel: {exc}')
