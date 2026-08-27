import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from app.services.action_runner import verify_action_token


class ActionTokenTests(TestCase):
    def test_matching_token_is_accepted(self):
        with TemporaryDirectory() as directory:
            token_file = Path(directory) / "token"
            token = "a" * 64
            token_file.write_text(token, encoding="utf-8")
            with patch.dict(os.environ, {"OPSDECK_ACTION_TOKEN_FILE": str(token_file)}):
                verify_action_token(token)

    def test_invalid_token_is_rejected(self):
        with TemporaryDirectory() as directory:
            token_file = Path(directory) / "token"
            token_file.write_text("a" * 64, encoding="utf-8")
            with patch.dict(os.environ, {"OPSDECK_ACTION_TOKEN_FILE": str(token_file)}):
                with self.assertRaises(PermissionError):
                    verify_action_token("b" * 64)

    def test_short_server_token_disables_actions(self):
        with TemporaryDirectory() as directory:
            token_file = Path(directory) / "token"
            token_file.write_text("short", encoding="utf-8")
            with patch.dict(os.environ, {"OPSDECK_ACTION_TOKEN_FILE": str(token_file)}):
                with self.assertRaises(RuntimeError):
                    verify_action_token("short")
