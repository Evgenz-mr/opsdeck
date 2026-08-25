import httpx

async def s3_health(cfg: dict) -> dict:
    endpoint = cfg['endpoint'].rstrip('/')
    verify = bool(cfg.get('verify_tls', True))
    timeout = float(cfg.get('timeout', 5))
    result = {'endpoint': endpoint, 'state': 'unknown'}
    try:
        async with httpx.AsyncClient(timeout=timeout, verify=verify) as client:
            r = await client.get(endpoint)
        result['status_code'] = r.status_code
        result['state'] = 'healthy' if r.status_code < 500 else 'degraded'
    except Exception as exc:
        result['state'] = 'degraded'
        result['error'] = str(exc)
    return result
