from datetime import datetime, timezone
from unittest import TestCase

from app.services.victoriametrics_health import certificate_lifetime


NOW = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)


def certificate_output(not_after: str, not_before: str = "Aug 1 00:00:00 2026 GMT"):
    return f"notBefore={not_before}\nnotAfter={not_after}\n"


class CertificateLifetimeTests(TestCase):
    def test_healthy_certificate(self):
        result = certificate_lifetime(certificate_output("Oct 15 12:00:00 2026 GMT"), NOW)
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["days_left"], 49)

    def test_warning_certificate(self):
        result = certificate_lifetime(certificate_output("Sep 16 12:00:00 2026 GMT"), NOW)
        self.assertEqual(result["status"], "warning")
        self.assertEqual(result["days_left"], 20)

    def test_critical_certificate(self):
        result = certificate_lifetime(certificate_output("Sep 2 12:00:00 2026 GMT"), NOW)
        self.assertEqual(result["status"], "critical")
        self.assertEqual(result["days_left"], 6)

    def test_expired_certificate(self):
        result = certificate_lifetime(certificate_output("Aug 26 12:00:00 2026 GMT"), NOW)
        self.assertEqual(result["status"], "expired")

    def test_not_yet_valid_certificate(self):
        result = certificate_lifetime(
            certificate_output(
                "Oct 15 12:00:00 2026 GMT",
                "Aug 28 00:00:00 2026 GMT",
            ),
            NOW,
        )
        self.assertEqual(result["status"], "invalid")
