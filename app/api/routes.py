import asyncio

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import select

from app.core.config import load_config
from app.core.db import AuditEvent, SessionLocal
from app.services.action_runner import run_ssh_action, verify_action_token
from app.services.kubernetes_health import namespace_health


router = APIRouter(prefix="/api")
ACTION_LOCKS: dict[tuple[str, str], asyncio.Lock] = {}


@router.get("/config")
async def get_config():
    return load_config()


@router.get("/health/kubernetes/{environment}/{namespace}")
async def k8s_health(environment: str, namespace: str):
    cfg = load_config()
    env = cfg.get("environments", {}).get(environment)
    if not env:
        raise HTTPException(404, "Unknown environment")
    kube = env.get("kubernetes", {})
    if namespace not in kube.get("namespaces", []):
        raise HTTPException(403, "Namespace is not allowed")
    return namespace_health(
        environment,
        kube.get("context", ""),
        namespace,
        kubeconfig_path=kube.get("kubeconfig"),
        mode=kube.get("mode", "kubeconfig"),
    )


@router.post("/actions/{environment}/{service}/{target}/{action_id}")
async def run_action(
    environment: str,
    service: str,
    target: str,
    action_id: str,
    x_opsdeck_action_token: str | None = Header(default=None),
):
    try:
        verify_action_token(x_opsdeck_action_token)
    except PermissionError as exc:
        raise HTTPException(401, str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc

    cfg = load_config()
    target_cfg = (
        cfg.get("services", {})
        .get(service, {})
        .get("targets", {})
        .get(environment, {})
        .get(target)
    )
    if not target_cfg:
        raise HTTPException(404, "Target not found")
    if action_id not in target_cfg.get("actions", []):
        raise HTTPException(403, "Action is not allowed for this target")

    lock = ACTION_LOCKS.setdefault((service, environment), asyncio.Lock())
    if lock.locked():
        raise HTTPException(409, "Another action is already running for this cluster")

    async with lock:
        try:
            status, output = await run_ssh_action(
                target_cfg["host"],
                target_cfg.get("user", "opsdeck"),
                action_id,
            )
        except Exception as exc:
            status, output = "failed", f"{type(exc).__name__}: {exc}"

        async with SessionLocal() as session:
            session.add(AuditEvent(
                environment=environment,
                service=service,
                target=target,
                action=action_id,
                status=status,
                output=output[-10000:],
            ))
            await session.commit()

    return {"status": status, "output": output}


@router.get("/audit")
async def audit():
    async with SessionLocal() as session:
        rows = (
            await session.execute(
                select(AuditEvent).order_by(AuditEvent.id.desc()).limit(100)
            )
        ).scalars().all()
    return [
        {
            "id": row.id,
            "created_at": row.created_at,
            "environment": row.environment,
            "service": row.service,
            "target": row.target,
            "action": row.action,
            "status": row.status,
        }
        for row in rows
    ]
