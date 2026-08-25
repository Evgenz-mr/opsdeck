from datetime import datetime, timezone


def maintenance_state(cfg: dict, environment: str, service: str) -> dict:
    entries = cfg.get('maintenance', [])
    now = datetime.now(timezone.utc)
    for item in entries:
        if item.get('environment') != environment or item.get('service') != service:
            continue
        until = datetime.fromisoformat(item['until'].replace('Z', '+00:00'))
        if until > now:
            return {'active': True, 'until': until.isoformat(), 'reason': item.get('reason', ''), 'owner': item.get('owner')}
    return {'active': False}
