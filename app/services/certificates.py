from datetime import datetime, timezone
import ssl, socket


def inspect_tls(host: str, port: int = 443, server_name: str | None = None, timeout: float = 5.0) -> dict:
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as raw:
        with ctx.wrap_socket(raw, server_hostname=server_name or host) as tls:
            cert = tls.getpeercert()
    not_after = cert.get('notAfter')
    expires = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
    days_left = (expires - datetime.now(timezone.utc)).days
    status = 'critical' if days_left < 10 else 'warning' if days_left < 30 else 'healthy'
    return {'host': host, 'port': port, 'expires_at': expires.isoformat(), 'days_left': days_left, 'status': status}
