def evaluate_cluster_safety(total_nodes: int, selected_nodes: int, min_healthy: int, currently_healthy: int | None = None) -> dict:
    healthy = currently_healthy if currently_healthy is not None else total_nodes
    remaining = healthy - selected_nodes
    allowed = selected_nodes > 0 and remaining >= min_healthy
    return {
        'allowed': allowed,
        'total_nodes': total_nodes,
        'currently_healthy': healthy,
        'selected_nodes': selected_nodes,
        'remaining_healthy': remaining,
        'minimum_healthy_required': min_healthy,
        'reason': 'safe' if allowed else 'operation would violate minimum healthy node policy',
    }

def evaluate_fraction(total_nodes: int, selected_nodes: int, max_fraction: float = 0.34) -> dict:
    fraction = 0 if total_nodes == 0 else selected_nodes / total_nodes
    allowed = 0 < fraction <= max_fraction
    return {'allowed': allowed, 'selected_fraction': fraction, 'max_fraction': max_fraction}
