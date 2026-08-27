from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.realtime import bus

router = APIRouter(prefix='/api/executions', tags=['executions'])

@router.get('/{execution_id}/events')
async def events(execution_id: str):
    return StreamingResponse(bus.stream(execution_id), media_type='text/event-stream')
