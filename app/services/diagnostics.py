from pathlib import Path
import yaml

RUNBOOKS_DIR = Path('/app/runbooks')


def load_runbook(runbook_id: str) -> dict:
    path = RUNBOOKS_DIR / f'{runbook_id}.yaml'
    if not path.exists():
        raise ValueError(f'Unknown runbook: {runbook_id}')
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def explain(runbook_id: str, observations: dict) -> dict:
    runbook = load_runbook(runbook_id)
    findings = []
    for rule in runbook.get('rules', []):
        key = rule['when']['field']
        op = rule['when'].get('op', 'eq')
        expected = rule['when']['value']
        actual = observations.get(key)
        matched = (op == 'eq' and actual == expected) or (op == 'gt' and actual is not None and actual > expected)
        if matched:
            findings.append({'id': rule['id'], 'severity': rule.get('severity', 'warning'), 'message': rule['message'], 'recommended_action': rule.get('recommended_action')})
    return {'runbook': runbook_id, 'findings': findings, 'resolved': len(findings) == 0}
