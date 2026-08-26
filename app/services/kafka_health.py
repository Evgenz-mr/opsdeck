import asyncio
import socket
import httpx

async def kafka_health(cfg: dict) -> dict:
    brokers = []
    for item in cfg.get('brokers', []):
        host = item['host']; port = int(item.get('port', 9092))
        try:
            await asyncio.to_thread(_tcp_probe, host, port, float(cfg.get('timeout', 3)))
            brokers.append({'host': host, 'port': port, 'state': 'healthy'})
        except Exception as exc:
            brokers.append({'host': host, 'port': port, 'state': 'degraded', 'error': str(exc)})

    exporter = None
    if cfg.get('exporter_url'):
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(cfg['exporter_url'])
            exporter = {'state': 'healthy' if r.status_code < 400 else 'degraded', 'status_code': r.status_code}
        except Exception as exc:
            exporter = {'state': 'degraded', 'error': str(exc)}

    healthy = all(x['state'] == 'healthy' for x in brokers) and (not exporter or exporter['state'] == 'healthy')
    return {'state': 'healthy' if healthy else 'degraded', 'brokers': brokers, 'exporter': exporter}

def _tcp_probe(host: str, port: int, timeout: float):
    with socket.create_connection((host, port), timeout=timeout):
        return True
