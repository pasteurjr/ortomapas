from fastapi import APIRouter, Depends, HTTPException
from backend.agents.llm_client import LMStudioClient
from backend.routers.auth import current_user

router = APIRouter()

@router.get('/agents/status')
async def agent_status(user: dict = Depends(current_user)):
    client = LMStudioClient()
    try:
        models = client.models(); available = [m.get('id') for m in models.get('data', [])]
        return {'online': True, 'base_url': client.base_url, 'configured_model': client.model, 'available_models': available}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f'LM Studio indisponivel: {exc}')
