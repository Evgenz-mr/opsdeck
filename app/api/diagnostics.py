from fastapi import APIRouter, HTTPException
from app.services.diagnostics import explain

router = APIRouter(prefix='/api/diagnostics', tags=['diagnostics'])

@router.post('/{runbook_id}')
async def diagnose(runbook_id: str, observations: dict):
    try:
        return explain(runbook_id, observations)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
