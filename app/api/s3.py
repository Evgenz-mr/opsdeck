from fastapi import APIRouter, HTTPException
from app.core.config import load_config
from app.services.s3_health import s3_health

router = APIRouter(prefix='/api/s3', tags=['s3'])

@router.get('/{environment}')
async def health(environment: str):
    cfg = load_config().get('services', {}).get('s3', {}).get('health', {}).get(environment)
    if not cfg:
        raise HTTPException(404, 'S3 health configuration not found')
    return await s3_health(cfg)
