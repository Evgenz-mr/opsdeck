def is_allowed(policy: dict, role: str, environment: str, action: str) -> bool:
    role_cfg = policy.get('roles', {}).get(role, {})
    envs = role_cfg.get('environments', [])
    actions = role_cfg.get('actions', [])
    env_ok = '*' in envs or environment in envs
    action_ok = '*' in actions or action in actions
    return env_ok and action_ok
