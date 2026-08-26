import asyncio
import socket
import httpx

async def postgres_health(cfg: dict) -> dict:
    nodes = []
    for item in cfg.get('nodes', []):
        host = item['host']; port = int(item.get('port', 5432))
        try:
            await asyncio.to_thread(_tcp_probe, host, port, float(cfg.get('timeout', 3)))
            nodes.append({'host': host, 'port': port, 'role': item.get('role', 'unknown'), 'state': 'healthy'})
        except Exception as exc:
            nodes.append({'host': host, 'port': port, 'role': item.get('role', 'unknown'), 'state': 'degraded', 'error': str(exc)})

    exporter = None
    if cfg.get('exporter_url'):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(cfg['exporter_url'])
            exporter = {'state': 'healthy' if r.status_code < 400 else 'degraded', 'status_code': r.status_code}
        except Exception as exc:
            exporter = {'state': 'degraded', 'error': str(exc)}

    primary_count = sum(1 for x in nodes if x.get('role') == 'primary' and x['state'] == 'healthy')
    state = 'healthy' if primary_count == 1 and all(x['state'] == 'healthy' for x in nodes) else 'degraded'
    return {'state': state, 'nodes': nodes, 'exporter': exporter, 'primary_count': primary_count}

def _tcp_probe(host: str, port: int, timeout: float):
    with socket.create_connection((host, port), timeout=timeout):
        return True
