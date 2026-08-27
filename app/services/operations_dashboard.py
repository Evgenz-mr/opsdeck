import asyncio
from app.core.config import load_config
from app.services.kubernetes_health import namespace_health

async def build_overview() -> dict:
    cfg = load_config()
    environments = []
    for name, env in cfg.get('environments', {}).items():
        kube = env.get('kubernetes', {})
        ns_results = []
        for namespace in kube.get('namespaces', []):
            result = await asyncio.to_thread(namespace_health, name, kube.get('context', ''), namespace)
            ns_results.append(result)
        environments.append({'name': name, 'kubernetes': ns_results})
    return {'environments': environments, 'approvals': cfg.get('approvals', {'enabled': False})}
