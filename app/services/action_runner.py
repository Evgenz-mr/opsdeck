import asyncio
import os
import re
import secrets
from pathlib import Path

import asyncssh
import yaml


ACTIONS_DIR = Path("/app/actions")
ACTION_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")


def load_action(action_id: str) -> dict:
    if not ACTION_ID_PATTERN.fullmatch(action_id):
        raise ValueError("Invalid action id")
    path = ACTIONS_DIR / f"{action_id}.yaml"
    if not path.is_file():
        raise ValueError(f"Unknown action: {action_id}")
    action = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if action.get("id") != action_id or action.get("runner") != "ssh" or not action.get("command"):
        raise ValueError(f"Invalid action definition: {action_id}")
    return action


def action_catalog() -> dict[str, dict]:
    catalog = {}
    for path in sorted(ACTIONS_DIR.glob("*.yaml")):
        try:
            action = load_action(path.stem)
        except ValueError:
            continue
        catalog[path.stem] = {
            "id": path.stem,
            "name": action.get("name", path.stem),
            "risk": action.get("risk", "unknown"),
        }
    return catalog


def verify_action_token(provided_token: str | None):
    token_file = Path(os.getenv("OPSDECK_ACTION_TOKEN_FILE", "/run/secrets/action-token"))
    try:
        expected_token = token_file.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError("Action API is disabled: action token file is unavailable") from exc
    if len(expected_token) < 32:
        raise RuntimeError("Action API is disabled: action token must contain at least 32 characters")
    if not provided_token or not secrets.compare_digest(provided_token, expected_token):
        raise PermissionError("Invalid action token")


async def run_ssh_action(host: str, user: str, action_id: str):
    action = load_action(action_id)
    timeout = int(action.get("timeout", 120))
    known_hosts = os.getenv("OPSDECK_SSH_KNOWN_HOSTS", "/home/opsdeck/.ssh/known_hosts")
    private_key = os.getenv("OPSDECK_SSH_PRIVATE_KEY", "/home/opsdeck/.ssh/id_ed25519")

    async with asyncssh.connect(
        host,
        username=user,
        known_hosts=known_hosts,
        client_keys=[private_key],
    ) as connection:
        result = await asyncio.wait_for(
            connection.run(action["command"], check=False),
            timeout=timeout,
        )
    status = "success" if result.exit_status == 0 else "failed"
    return status, (result.stdout or "") + (result.stderr or "")
