from types import SimpleNamespace
from unittest import TestCase

from app.services.kubernetes_health import _container_details, _parse_image_reference


class ImageReferenceTests(TestCase):
    def test_registry_port_does_not_become_a_tag(self):
        parsed = _parse_image_reference("registry.example:5000/team/api:1.2.3")

        self.assertEqual(parsed["repository"], "registry.example:5000/team/api")
        self.assertEqual(parsed["tag"], "1.2.3")
        self.assertEqual(parsed["version"], "1.2.3")

    def test_digest_is_used_as_version_without_tag(self):
        parsed = _parse_image_reference("team/api@sha256:abc")

        self.assertEqual(parsed["repository"], "team/api")
        self.assertIsNone(parsed["tag"])
        self.assertEqual(parsed["digest"], "sha256:abc")
        self.assertEqual(parsed["version"], "sha256:abc")

    def test_container_details_prefer_version_label_and_include_actual_digest(self):
        container = SimpleNamespace(
            name="api",
            image="registry.example:5000/team/api:1.2.3",
        )
        status = SimpleNamespace(
            name="api",
            image_id="docker-pullable://registry.example/team/api@sha256:def",
            ready=True,
            restart_count=2,
        )

        details = _container_details(
            [container],
            [status],
            {
                "app.kubernetes.io/name": "orders",
                "app.kubernetes.io/version": "2026.08",
            },
        )[0]

        self.assertEqual(details["service"], "orders")
        self.assertEqual(details["version"], "2026.08")
        self.assertEqual(details["tag"], "1.2.3")
        self.assertEqual(details["actual_digest"], "sha256:def")
        self.assertTrue(details["ready"])
        self.assertEqual(details["restarts"], 2)
