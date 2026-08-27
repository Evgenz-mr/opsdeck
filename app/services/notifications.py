import httpx

async def send_webhook(url: str, event: dict) -> dict:
    async with httpx.AsyncClient(timeout=5) as client:
        response = await client.post(url, json=event)
    return {'status_code': response.status_code, 'ok': response.status_code < 400}
