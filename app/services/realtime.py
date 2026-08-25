import asyncio
import json
from collections import defaultdict

class EventBus:
    def __init__(self):
        self._queues: dict[str, list[asyncio.Queue]] = defaultdict(list)

    async def publish(self, execution_id: str, event: dict):
        payload = {'execution_id': execution_id, **event}
        for queue in list(self._queues[execution_id]):
            await queue.put(payload)

    async def stream(self, execution_id: str):
        queue = asyncio.Queue(maxsize=100)
        self._queues[execution_id].append(queue)
        try:
            while True:
                item = await queue.get()
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
                if item.get('terminal'):
                    break
        finally:
            self._queues[execution_id].remove(queue)

bus = EventBus()
