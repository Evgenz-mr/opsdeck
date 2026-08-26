from datetime import datetime

def merge_events(*sources: list[dict]) -> list[dict]:
    events = []
    for source in sources:
        events.extend(source)
    def ts(item):
        value = item.get('timestamp') or item.get('created_at')
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except Exception:
            return datetime.min
    return sorted(events, key=ts)
