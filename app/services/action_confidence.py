def confidence(history: list[dict]) -> dict:
    total = len(history)
    success = sum(1 for item in history if item.get('status') == 'success')
    failed = total - success
    rate = 1.0 if total == 0 else success / total
    return {'executions': total, 'successes': success, 'failures': failed, 'success_rate': rate}
