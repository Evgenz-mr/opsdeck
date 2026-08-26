def compare_snapshots(left: dict, right: dict) -> dict:
    keys = sorted(set(left) | set(right))
    diffs = []
    for key in keys:
        a = left.get(key)
        b = right.get(key)
        if a != b:
            diffs.append({'field': key, 'left': a, 'right': b})
    return {'equal': not diffs, 'differences': diffs}
