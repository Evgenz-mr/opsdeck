import asyncio
from app.services.action_runner import run_ssh_action

async def run_rolling(targets: list[dict], action_id: str, batch_size: int = 1, pause_seconds: float = 2.0) -> dict:
    results = []
    for i in range(0, len(targets), batch_size):
        batch = targets[i:i + batch_size]
        current = await asyncio.gather(*[
            run_ssh_action(t['host'], t.get('user', 'opsdeck'), action_id)
            for t in batch
        ], return_exceptions=True)
        failed = False
        for target, result in zip(batch, current):
            if isinstance(result, Exception):
                results.append({'target': target['name'], 'status': 'failed', 'output': str(result)})
                failed = True
                continue
            status, output = result
            results.append({'target': target['name'], 'status': status, 'output': output[-4000:]})
            if status != 'success':
                failed = True
        if failed:
            return {'status': 'paused', 'results': results, 'remaining': len(targets) - len(results)}
        if i + batch_size < len(targets):
            await asyncio.sleep(pause_seconds)
    return {'status': 'success', 'results': results, 'remaining': 0}
