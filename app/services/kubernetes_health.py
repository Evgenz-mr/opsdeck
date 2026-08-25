from kubernetes import client, config
def namespace_health(environment: str, context: str, namespace: str):
    try:
        config.load_kube_config(context=context)
        core = client.CoreV1Api(); apps = client.AppsV1Api()
        pods = core.list_namespaced_pod(namespace).items
        deps = apps.list_namespaced_deployment(namespace).items
        out = {"environment": environment, "namespace": namespace, "state": "healthy", "deployments": [], "pods": []}
        for d in deps:
            desired = d.spec.replicas or 0; ready = d.status.ready_replicas or 0
            state = "healthy" if desired == ready else "degraded"
            if state != "healthy": out["state"] = "degraded"
            out["deployments"].append({"name": d.metadata.name, "ready": ready, "desired": desired, "state": state})
        for p in pods:
            restarts = sum((c.restart_count or 0) for c in (p.status.container_statuses or []))
            waiting = [c.state.waiting.reason for c in (p.status.container_statuses or []) if c.state and c.state.waiting and c.state.waiting.reason]
            state = "healthy" if p.status.phase in ("Running","Succeeded") and not waiting else "degraded"
            if state != "healthy": out["state"] = "degraded"
            out["pods"].append({"name": p.metadata.name, "phase": p.status.phase, "restarts": restarts, "waiting": waiting, "state": state})
        return out
    except Exception as exc:
        return {"environment": environment, "namespace": namespace, "state": "unknown", "error": str(exc)}
