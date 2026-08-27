from fastapi import APIRouter, HTTPException

from app.core.config import load_config
from app.services.victoriametrics_health import cluster_health


router = APIRouter(prefix="/api/victoriametrics", tags=["victoriametrics"])


@router.get("/{environment}")
async def health(environment: str):
    targets = (
        load_config()
        .get("services", {})
        .get("victoriametrics", {})
        .get("targets", {})
        .get(environment)
    )
    if not targets:
        raise HTTPException(404, "VictoriaMetrics configuration not found")
    return await cluster_health(targets)
