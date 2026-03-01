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
_config.client = MagicMock()
sys.modules["config"] = _config

_mistralai = types.ModuleType("mistralai")
_mistralai.Mistral = lambda **kw: None
sys.modules.setdefault("mistralai", _mistralai)

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
