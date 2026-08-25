from pathlib import Path
import os, yaml
CONFIG_PATH = os.getenv("OPSDECK_CONFIG", "/app/config/opsdeck.yaml")
def load_config() -> dict:
    p = Path(CONFIG_PATH)
    if not p.exists():
        return {"approvals": {"enabled": False}, "environments": {}, "services": {}}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
