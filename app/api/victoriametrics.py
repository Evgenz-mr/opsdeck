from fastapi import APIRouter, HTTPException
from app.core.config import load_config
from app.services.victoriametrics_health import cluster_health

router = APIRouter(prefix='/api/victoriametrics', tags=['victoriametrics'])

@router.get('/{environment}')
async def health(environment: str):
    cfg = load_config().get('services', {}).get('victoriametrics', {}).get('health', {}).get(environment)
    if not cfg:
        raise HTTPException(404, 'VictoriaMetrics health configuration not found')
    return await cluster_health(cfg)
