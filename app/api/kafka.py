from fastapi import APIRouter, HTTPException
from app.core.config import load_config
from app.services.kafka_health import kafka_health

router = APIRouter(prefix='/api/kafka', tags=['kafka'])

@router.get('/{environment}')
async def health(environment: str):
    cfg = load_config().get('services', {}).get('kafka', {}).get('health', {}).get(environment)
    if not cfg:
        raise HTTPException(404, 'Kafka health configuration not found')
    return await kafka_health(cfg)
