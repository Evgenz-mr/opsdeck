from fastapi import APIRouter
from app.services.operations_dashboard import build_overview

router = APIRouter(prefix='/api/operations', tags=['operations'])

@router.get('/overview')
async def overview():
    return await build_overview()
