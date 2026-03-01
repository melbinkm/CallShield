"""Tests for the auth module."""

import json
import os
import importlib.util
import pytest
from unittest.mock import patch

# conftest.py stubs auth before app import, but we need to test the real module.
# Load the real auth module from disk, bypassing sys.modules stub.
_spec = importlib.util.spec_from_file_location(
    "auth_real",
    os.path.join(os.path.dirname(__file__), "..", "auth.py"),
)
auth = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(auth)


class TestAuthDisabled:
    """Tests for dev mode (no keys configured)."""

    def test_no_keys_file_auth_disabled(self, tmp_path):
        missing = str(tmp_path / "nonexistent.json")
        with patch.object(auth, "API_KEYS_FILE", missing):
            assert auth.is_auth_enabled() is False

    def test_empty_keys_auth_disabled(self, tmp_path):
        f = tmp_path / "keys.json"
        f.write_text("{}")
        with patch.object(auth, "API_KEYS_FILE", str(f)):
            assert auth.is_auth_enabled() is False

    def test_malformed_json_auth_disabled(self, tmp_path):
        f = tmp_path / "keys.json"
        f.write_text("{bad json!!")
        with patch.object(auth, "API_KEYS_FILE", str(f)):
            assert auth.is_auth_enabled() is False


class TestKeyVerification:
    """Tests for API key validation."""

    @pytest.fixture
    def keys_file(self, tmp_path):
        f = tmp_path / "keys.json"
        keys = {
            "cs_valid_key_123": {"name": "test", "active": True},
            "cs_inactive_key": {"name": "disabled", "active": False},
        }
        f.write_text(json.dumps(keys))
        return str(f)

    def test_valid_key_accepted(self, keys_file):
        with patch.object(auth, "API_KEYS_FILE", keys_file):
            assert auth.verify_api_key("cs_valid_key_123") is True

    def test_invalid_key_rejected(self, keys_file):
        with patch.object(auth, "API_KEYS_FILE", keys_file):
            assert auth.verify_api_key("cs_wrong_key") is False

    def test_inactive_key_rejected(self, keys_file):
        with patch.object(auth, "API_KEYS_FILE", keys_file):
            assert auth.verify_api_key("cs_inactive_key") is False


class TestWebSocketAuth:
    """Tests for WebSocket API key verification."""

    def test_ws_auth_disabled_allows_none(self, tmp_path):
        missing = str(tmp_path / "nonexistent.json")
        with patch.object(auth, "API_KEYS_FILE", missing):
            assert auth.verify_ws_api_key(None) is True

    def test_ws_valid_key_accepted(self, tmp_path):
        f = tmp_path / "keys.json"
        keys = {"cs_ws_key": {"name": "ws-test", "active": True}}
        f.write_text(json.dumps(keys))
        with patch.object(auth, "API_KEYS_FILE", str(f)):
            assert auth.verify_ws_api_key("cs_ws_key") is True

    def test_ws_invalid_key_rejected(self, tmp_path):
        f = tmp_path / "keys.json"
        keys = {"cs_ws_key": {"name": "ws-test", "active": True}}
        f.write_text(json.dumps(keys))
        with patch.object(auth, "API_KEYS_FILE", str(f)):
            assert auth.verify_ws_api_key("cs_bad_key") is False
