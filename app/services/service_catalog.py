from app.core.config import load_config

def catalog() -> list[dict]:
    cfg = load_config()
    items = []
    for service_id, service in cfg.get('services', {}).items():
        environments = sorted(service.get('targets', {}).keys())
        items.append({
            'id': service_id,
            'name': service.get('display_name', service_id),
            'type': service.get('type', 'service'),
            'description': service.get('description', ''),
            'environments': environments,
            'owner': service.get('owner'),
            'links': service.get('links', {}),
        })
    return items
