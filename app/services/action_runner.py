from pathlib import Path
import asyncio, asyncssh, yaml
ACTIONS_DIR = Path("/app/actions")
def load_action(action_id: str) -> dict:
    p = ACTIONS_DIR / f"{action_id}.yaml"
    if not p.exists(): raise ValueError(f"Unknown action: {action_id}")
    return yaml.safe_load(p.read_text(encoding="utf-8"))
async def run_ssh_action(host: str, user: str, action_id: str):
    action = load_action(action_id)
    timeout = int(action.get("timeout", 120))
    async with asyncssh.connect(host, username=user, known_hosts=None) as conn:
        result = await asyncio.wait_for(conn.run(action["command"], check=False), timeout=timeout)
    status = "success" if result.exit_status == 0 else "failed"
    return status, (result.stdout or "") + (result.stderr or "")
