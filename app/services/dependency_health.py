import httpx

async def check_http_dependencies(items: list[dict]) -> list[dict]:
    results = []
    async with httpx.AsyncClient(timeout=5) as client:
        for item in items:
            try:
                response = await client.get(item['url'])
                results.append({'name': item['name'], 'state': 'healthy' if response.status_code < 400 else 'degraded', 'status_code': response.status_code})
            except Exception as exc:
                results.append({'name': item['name'], 'state': 'degraded', 'error': str(exc)})
    return results

def blast_radius(graph: dict[str, list[str]], failed_service: str) -> list[str]:
    return sorted([name for name, deps in graph.items() if failed_service in deps])
