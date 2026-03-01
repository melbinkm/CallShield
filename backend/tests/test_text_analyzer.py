"""Tests for services/text_analyzer.py with mocked Mistral client."""

import sys
import os
import types
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

from services.text_analyzer import analyze_transcript
from prompts.templates import SCAM_TEXT_PROMPT


def _make_mock_response(content):
    """Create a mock Mistral API response."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


class TestAnalyzeTranscript:
    def test_prompt_includes_transcript(self):
        transcript = "Hello, this is a test."
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response('{"ok": true}')

        with patch("services.text_analyzer.client", mock_client):
            asyncio.run(analyze_transcript(transcript))

        call_kwargs = mock_client.chat.complete.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        if messages is None:
            # functools.partial passes as keyword args
            messages = call_kwargs[0][0] if call_kwargs[0] else None
        content = messages[0]["content"]
        assert SCAM_TEXT_PROMPT in content
        assert transcript in content

    def test_model_selection(self):
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response('{"ok": true}')

        with patch("services.text_analyzer.client", mock_client):
            asyncio.run(analyze_transcript("test"))

        call_kwargs = mock_client.chat.complete.call_args
        model = call_kwargs.kwargs.get("model") or call_kwargs[1].get("model")
        assert model == "mistral-large-latest"

    def test_response_format(self):
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response('{"ok": true}')

        with patch("services.text_analyzer.client", mock_client):
            asyncio.run(analyze_transcript("test"))

        call_kwargs = mock_client.chat.complete.call_args
        fmt = call_kwargs.kwargs.get("response_format") or call_kwargs[1].get("response_format")
        assert fmt == {"type": "json_object"}

    def test_successful_response(self):
        expected = '{"scam_score": 0.5, "verdict": "SUSPICIOUS"}'
        mock_client = MagicMock()
        mock_client.chat.complete.return_value = _make_mock_response(expected)

        with patch("services.text_analyzer.client", mock_client):
            result = asyncio.run(analyze_transcript("test transcript"))
        assert result == expected

    def test_client_error_propagates(self):
        mock_client = MagicMock()
        mock_client.chat.complete.side_effect = RuntimeError("Connection failed")

        with patch("services.text_analyzer.client", mock_client):
            with pytest.raises(RuntimeError, match="Connection failed"):
                asyncio.run(analyze_transcript("test"))
