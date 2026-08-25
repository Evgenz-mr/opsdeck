from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.core.config import load_config
from app.core.db import SessionLocal, AuditEvent
from app.services.action_runner import run_ssh_action
from app.services.kubernetes_health import namespace_health
router = APIRouter(prefix="/api")
@router.get("/config")
async def get_config(): return load_config()
@router.get("/health/kubernetes/{environment}/{namespace}")
async def k8s_health(environment: str, namespace: str):
    cfg = load_config(); env = cfg.get("environments", {}).get(environment)
    if not env: raise HTTPException(404, "Unknown environment")
    kube = env.get("kubernetes", {})
    if namespace not in kube.get("namespaces", []): raise HTTPException(403, "Namespace is not allowed")
    return namespace_health(environment, kube.get("context", ""), namespace)
@router.post("/actions/{environment}/{service}/{target}/{action_id}")
async def run_action(environment: str, service: str, target: str, action_id: str):
    cfg = load_config()
    target_cfg = cfg.get("services",{}).get(service,{}).get("targets",{}).get(environment,{}).get(target)
    if not target_cfg: raise HTTPException(404, "Target not found")
    if action_id not in target_cfg.get("actions", []): raise HTTPException(403, "Action is not allowed")
    status, output = await run_ssh_action(target_cfg["host"], target_cfg.get("user","opsdeck"), action_id)
    async with SessionLocal() as s:
        s.add(AuditEvent(environment=environment, service=service, target=target, action=action_id, status=status, output=output[-10000:]))
        await s.commit()
    return {"status": status, "output": output}
@router.get("/audit")
async def audit():
    async with SessionLocal() as s:
        rows = (await s.execute(select(AuditEvent).order_by(AuditEvent.id.desc()).limit(100))).scalars().all()
    return [{"id":r.id,"created_at":r.created_at,"environment":r.environment,"service":r.service,"target":r.target,"action":r.action,"status":r.status} for r in rows]
