import asyncio
from fastapi import APIRouter, HTTPException
from app.core.config import load_config
from app.services.certificates import inspect_tls

router = APIRouter(prefix='/api/certificates', tags=['certificates'])

@router.get('/{service}/{environment}/{target}')
async def certificate_status(service: str, environment: str, target: str):
    cfg = load_config()
    item = cfg.get('services', {}).get(service, {}).get('targets', {}).get(environment, {}).get(target)
    if not item:
        raise HTTPException(404, 'Target not found')
    host = item['host']
    port = int(item.get('tls_port', 443))
    return await asyncio.to_thread(inspect_tls, host, port, item.get('server_name'))
