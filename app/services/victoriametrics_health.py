import asyncio
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from app.services.action_runner import run_ssh_command


CERTIFICATE_COMMAND = (
    "/usr/bin/sudo -n /usr/bin/openssl x509 "
    "-in /opt/victoria-metrics/certs/tls.crt "
    "-noout -subject -issuer -serial -dates"
)
SERVICE_UNITS = {
    "vminsert": "vminsert.service",
    "vmselect": "vmselect.service",
    "vmstorage": "vmstorage.service",
}


def certificate_lifetime(output: str, now: datetime | None = None) -> dict:
    values = {}
    for line in output.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()

    if not_after := values.get("notAfter"):
        expires = parsedate_to_datetime(not_after).astimezone(timezone.utc)
    else:
        raise ValueError("Certificate expiry date is unavailable")

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    days_left = (expires - current).days

    not_before = values.get("notBefore")
    starts = parsedate_to_datetime(not_before).astimezone(timezone.utc) if not_before else None
    if starts and current < starts:
        status = "invalid"
    elif expires <= current:
        status = "expired"
    elif days_left < 10:
        status = "critical"
    elif days_left < 30:
        status = "warning"
    else:
        status = "healthy"

    return {
        "status": status,
        "expires_at": expires.isoformat(),
        "days_left": days_left,
    }


async def component_status(target_id: str, target: dict) -> dict:
    role = target.get("role", "")
    unit = SERVICE_UNITS.get(role)
    result = {
        "id": target_id,
        "name": target.get("display_name", target_id),
        "role": role,
        "service": "unknown",
        "certificate": {"status": "unknown"},
    }
    if not unit:
        result["error"] = "Unsupported VictoriaMetrics role"
        return result
    try:
        service_status, service_output = await run_ssh_command(
            target["host"],
            target.get("user", "opsdeck"),
            f"/usr/bin/systemctl is-active {unit}",
            15,
        )
        result["service"] = "active" if service_status == "success" and service_output.strip() == "active" else "inactive"

        cert_status, cert_output = await run_ssh_command(
            target["host"],
            target.get("user", "opsdeck"),
            CERTIFICATE_COMMAND,
            20,
        )
        if cert_status == "success":
            result["certificate"] = certificate_lifetime(cert_output)
        else:
            result["error"] = "Certificate check failed"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


async def cluster_health(targets: dict) -> dict:
    components = await asyncio.gather(*(
        component_status(target_id, target)
        for target_id, target in targets.items()
    ))
    statuses = [component["certificate"]["status"] for component in components]
    if any(component["service"] != "active" for component in components) or any(
        status in {"critical", "expired", "invalid", "unknown"} for status in statuses
    ):
        state = "critical"
    elif "warning" in statuses:
        state = "warning"
    else:
        state = "healthy"
    return {"state": state, "components": components}
