"""Tests for services/audio_analyzer.py with mocked urllib."""

import sys
import os
import types
import json
import base64
import asyncio
import pytest
from unittest.mock import patch, MagicMock

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
sys.modules.setdefault("config", _config)

_mistralai = types.ModuleType("mistralai")
_mistralai.Mistral = lambda **kw: None
sys.modules.setdefault("mistralai", _mistralai)

from services.audio_analyzer import analyze_audio


def _mock_api_response(body_dict):
    """Create a mock urllib response with JSON body."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(body_dict).encode()
    return mock_resp


class TestAnalyzeAudio:
    def test_payload_construction(self):
        audio = b"fake wav bytes"
        resp = _mock_api_response({
            "choices": [{"message": {"content": '{"scam_score": 0.1}'}}]
        })
        with patch("urllib.request.urlopen", return_value=resp) as mock_urlopen:
            asyncio.run(analyze_audio(audio))

            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            assert request.full_url == "https://api.mistral.ai/v1/chat/completions"
            assert request.get_header("Authorization") == "Bearer test-key"
            assert request.get_header("Content-type") == "application/json"

            payload = json.loads(request.data)
            assert payload["model"] == "voxtral-mini-latest"
            assert payload["temperature"] == 0.3
            assert payload["response_format"] == {"type": "json_object"}

    def test_base64_encoding(self):
        audio = b"\x01\x02\x03\x04\x05"
        expected_b64 = base64.b64encode(audio).decode("utf-8")
        resp = _mock_api_response({
            "choices": [{"message": {"content": '{"ok": true}'}}]
        })
        with patch("urllib.request.urlopen", return_value=resp) as mock_urlopen:
            asyncio.run(analyze_audio(audio))
            payload = json.loads(mock_urlopen.call_args[0][0].data)
            actual_b64 = payload["messages"][0]["content"][0]["input_audio"]["data"]
            assert actual_b64 == expected_b64

    def test_successful_response(self):
        content_str = '{"scam_score": 0.7, "verdict": "LIKELY_SCAM"}'
        resp = _mock_api_response({
            "choices": [{"message": {"content": content_str}}]
        })
        with patch("urllib.request.urlopen", return_value=resp):
            result = asyncio.run(analyze_audio(b"audio"))
        assert result == content_str

    def test_empty_choices_raises(self):
        resp = _mock_api_response({"choices": []})
        with patch("urllib.request.urlopen", return_value=resp):
            with pytest.raises(ValueError, match="no choices"):
                asyncio.run(analyze_audio(b"audio"))

    def test_no_choices_key_raises(self):
        resp = _mock_api_response({"result": "unexpected"})
        with patch("urllib.request.urlopen", return_value=resp):
            with pytest.raises(ValueError, match="no choices"):
                asyncio.run(analyze_audio(b"audio"))

    def test_empty_content_raises(self):
        resp = _mock_api_response({
            "choices": [{"message": {"content": ""}}]
        })
        with patch("urllib.request.urlopen", return_value=resp):
            with pytest.raises(ValueError, match="Empty content"):
                asyncio.run(analyze_audio(b"audio"))

    def test_response_closed(self):
        resp = _mock_api_response({"choices": []})
        with patch("urllib.request.urlopen", return_value=resp):
            try:
                asyncio.run(analyze_audio(b"audio"))
            except ValueError:
                pass
        resp.close.assert_called_once()
