import httpx

async def check_component(name: str, url: str, timeout: float = 5.0) -> dict:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
        return {'name': name, 'url': url, 'state': 'healthy' if r.status_code < 400 else 'degraded', 'status_code': r.status_code}
    except Exception as exc:
        return {'name': name, 'url': url, 'state': 'degraded', 'error': str(exc)}

async def cluster_health(cfg: dict) -> dict:
    components = []
    for item in cfg.get('components', []):
        components.append(await check_component(item['name'], item['health_url'], float(cfg.get('timeout', 5))))
    state = 'healthy' if components and all(x['state'] == 'healthy' for x in components) else 'degraded'
    return {'state': state, 'components': components}
