"""Shared fixtures and module stubs for all backend tests."""

import sys
import os
import types
import struct
import pytest
from unittest.mock import MagicMock

# ── Module stubs (must run before any backend imports) ────────────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_config = types.ModuleType("config")
_config.MISTRAL_API_KEY = "test-key"
_config.AUDIO_MODEL = "voxtral-mini-latest"
_config.TEXT_MODEL = "mistral-large-latest"
_config.MAX_AUDIO_SIZE_MB = 25
_config.MAX_TRANSCRIPT_LENGTH = 10000
_config.THRESHOLD_SAFE = 0.30
_config.THRESHOLD_SUSPICIOUS = 0.60
_config.THRESHOLD_LIKELY_SCAM = 0.85
_config.DEMO_MODE = False
_config.client = MagicMock()
sys.modules["config"] = _config

_mistralai = types.ModuleType("mistralai")
_mistralai.Mistral = lambda **kw: None
sys.modules.setdefault("mistralai", _mistralai)

# ── Auth & rate-limit stubs (before app import) ──────────────────────────────

# Stub slowapi so it works without installation during basic tests
_slowapi = types.ModuleType("slowapi")
_slowapi_util = types.ModuleType("slowapi.util")
_slowapi_errors = types.ModuleType("slowapi.errors")


class _StubLimiter:
    """No-op limiter that passes through all requests."""
    def __init__(self, **kw):
        pass

    def limit(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator


_slowapi.Limiter = _StubLimiter
_slowapi_util.get_remote_address = lambda: "127.0.0.1"
_slowapi_errors.RateLimitExceeded = type("RateLimitExceeded", (Exception,), {})
sys.modules.setdefault("slowapi", _slowapi)
sys.modules.setdefault("slowapi.util", _slowapi_util)
sys.modules.setdefault("slowapi.errors", _slowapi_errors)

# Stub rate_limit module
_rate_limit = types.ModuleType("rate_limit")
_rate_limit.limiter = _StubLimiter()
sys.modules["rate_limit"] = _rate_limit

# Stub auth module — disable auth so existing tests pass unchanged
_auth = types.ModuleType("auth")
_auth.is_auth_enabled = lambda: False
_auth.verify_api_key = lambda key: True
_auth.verify_ws_api_key = lambda key: True


async def _noop_require_api_key(api_key=None):
    return None


_auth.require_api_key = _noop_require_api_key
sys.modules["auth"] = _auth

# Eagerly import app so all modules are cached with correct stubs
from main import app as _app
from fastapi.testclient import TestClient


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """FastAPI TestClient for HTTP and WebSocket tests."""
    return TestClient(_app)


def _make_valid_wav(pcm_samples=None):
    """Build a minimal valid WAV file (44-byte header + PCM data)."""
    if pcm_samples is None:
        pcm_data = b"\x00\x00" * 100  # 100 silent 16-bit samples
    else:
        pcm_data = struct.pack(f"<{len(pcm_samples)}h", *pcm_samples)

    data_size = len(pcm_data)
    file_size = 36 + data_size

    header = b"RIFF"
    header += struct.pack("<I", file_size)
    header += b"WAVE"
    header += b"fmt "
    header += struct.pack("<I", 16)  # fmt chunk size
    header += struct.pack("<HHIIHH", 1, 1, 16000, 32000, 2, 16)  # PCM mono 16kHz 16-bit
    header += b"data"
    header += struct.pack("<I", data_size)

    return header + pcm_data


@pytest.fixture
def make_valid_wav():
    """Fixture returning a WAV-builder function."""
    return _make_valid_wav
