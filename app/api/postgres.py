from fastapi import APIRouter, HTTPException
from app.core.config import load_config
from app.services.postgres_health import postgres_health

router = APIRouter(prefix='/api/postgres', tags=['postgres'])

@router.get('/{environment}')
async def health(environment: str):
    cfg = load_config().get('services', {}).get('postgres', {}).get('health', {}).get(environment)
    if not cfg:
        raise HTTPException(404, 'PostgreSQL health configuration not found')
    return await postgres_health(cfg)
