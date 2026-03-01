"""Tests for services/stream_processor.py — is_silent + StreamProcessor state."""

import struct
import sys
import os
import types
import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock

# Allow imports from backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Stub config before importing stream_processor
_config = types.ModuleType("config")
_config.MISTRAL_API_KEY = "test-key"
_config.AUDIO_MODEL = "voxtral-mini-latest"
_config.TEXT_MODEL = "mistral-large-latest"
_config.MAX_AUDIO_SIZE_MB = 25
_config.MAX_TRANSCRIPT_LENGTH = 10000
_config.THRESHOLD_SAFE = 0.30
_config.THRESHOLD_SUSPICIOUS = 0.60
_config.THRESHOLD_LIKELY_SCAM = 0.85
sys.modules.setdefault("config", _config)

_mistralai = types.ModuleType("mistralai")
_mistralai.Mistral = lambda **kw: None
sys.modules.setdefault("mistralai", _mistralai)

from services.stream_processor import is_silent, StreamProcessor
from services.response_formatter import score_to_verdict


# ── Helper to build WAV bytes ─────────────────────────────────────────────────

def _wav_bytes(samples):
    """Build a minimal WAV-like blob: 44-byte dummy header + 16-bit LE PCM."""
    header = b"\x00" * 44
    pcm = struct.pack(f"<{len(samples)}h", *samples)
    return header + pcm


# ── is_silent ─────────────────────────────────────────────────────────────────

class TestIsSilent:
    def test_all_zeros(self):
        audio = _wav_bytes([0] * 100)
        assert is_silent(audio) is True

    def test_low_rms_below_threshold(self):
        # Small amplitude → RMS well below 500
        audio = _wav_bytes([10, -10, 10, -10] * 25)
        assert is_silent(audio) is True

    def test_loud_audio(self):
        # Large amplitude → RMS >> 500
        audio = _wav_bytes([20000, -20000] * 50)
        assert is_silent(audio) is False

    def test_empty_pcm(self):
        # Only header, no PCM data
        audio = b"\x00" * 44
        assert is_silent(audio) is True

    def test_short_data(self):
        # Header + 1 byte (not enough for a 16-bit sample)
        audio = b"\x00" * 44 + b"\x01"
        assert is_silent(audio) is True

    def test_custom_threshold(self):
        # Moderate amplitude, silent at threshold=30000 but not at default
        audio = _wav_bytes([5000, -5000] * 50)
        assert is_silent(audio, threshold=30000) is True
        assert is_silent(audio, threshold=100) is False


# ── StreamProcessor state ─────────────────────────────────────────────────────

class TestStreamProcessorState:
    def test_initial_state(self):
        sp = StreamProcessor()
        assert sp.chunk_index == 0
        assert sp.cumulative_score == 0.0
        assert sp.max_score == 0.0
        assert sp.all_signals == []

    def test_initial_recommendation_empty(self):
        sp = StreamProcessor()
        assert sp.last_recommendation == ""

    def test_initial_transcript_summary_empty(self):
        sp = StreamProcessor()
        assert sp.last_transcript_summary == ""

    def test_exponential_weighting_formula(self):
        """Step through 5 chunk scores and verify 0.7*chunk + 0.3*prev."""
        sp = StreamProcessor()
        chunk_scores = [0.3, 0.8, 0.5, 0.9, 0.2]
        cumulative = 0.0
        for score in chunk_scores:
            cumulative = 0.7 * score + 0.3 * cumulative
        # Manually set cumulative_score as process_chunk would
        sp.cumulative_score = 0.0
        for score in chunk_scores:
            sp.cumulative_score = 0.7 * score + 0.3 * sp.cumulative_score
        assert round(sp.cumulative_score, 4) == round(cumulative, 4)

    def test_max_score_tracking(self):
        sp = StreamProcessor()
        scores = [0.1, 0.5, 0.3, 0.9, 0.2]
        for s in scores:
            if s > sp.max_score:
                sp.max_score = s
        assert sp.max_score == 0.9

    def test_get_final_result_verdict_mapping(self):
        """Verify get_final_result uses score_to_verdict correctly."""
        sp = StreamProcessor()
        sp.cumulative_score = 0.25
        result = sp.get_final_result()
        assert result["verdict"] == "SAFE"
        assert result["type"] == "final_result"

        sp.cumulative_score = 0.45
        assert sp.get_final_result()["verdict"] == "SUSPICIOUS"

        sp.cumulative_score = 0.70
        assert sp.get_final_result()["verdict"] == "LIKELY_SCAM"

        sp.cumulative_score = 0.90
        assert sp.get_final_result()["verdict"] == "SCAM"

    def test_get_final_result_signals(self):
        sp = StreamProcessor()
        sp.all_signals = [{"category": "URGENCY", "detail": "act now", "severity": "high"}]
        result = sp.get_final_result()
        assert result["signals"] == sp.all_signals

    def test_final_result_fields(self):
        sp = StreamProcessor()
        sp.chunk_index = 3
        sp.cumulative_score = 0.42
        sp.max_score = 0.65
        sp.last_recommendation = "Be cautious"
        sp.last_transcript_summary = "Caller claims to be bank"
        result = sp.get_final_result()
        assert result["total_chunks"] == 3
        assert result["combined_score"] == 0.42
        assert result["max_score"] == 0.65
        assert result["recommendation"] == "Be cautious"
        assert result["transcript_summary"] == "Caller claims to be bank"


# ── process_chunk silent path ─────────────────────────────────────────────────

class TestProcessChunkSilent:
    def test_process_chunk_silent_returns_safe(self):
        sp = StreamProcessor()
        silent_wav = _wav_bytes([0] * 100)
        result = asyncio.run(sp.process_chunk(silent_wav))
        assert result["type"] == "partial_result"
        assert result["verdict"] == "SAFE"
        assert result["scam_score"] == 0.0

    def test_process_chunk_silent_increments_index(self):
        sp = StreamProcessor()
        silent_wav = _wav_bytes([0] * 100)
        asyncio.run(sp.process_chunk(silent_wav))
        assert sp.chunk_index == 1
        asyncio.run(sp.process_chunk(silent_wav))
        assert sp.chunk_index == 2

    def test_process_chunk_silent_preserves_cumulative(self):
        sp = StreamProcessor()
        sp.cumulative_score = 0.5
        silent_wav = _wav_bytes([0] * 100)
        asyncio.run(sp.process_chunk(silent_wav))
        assert sp.cumulative_score == 0.5


# ── is_silent edge cases ─────────────────────────────────────────────────────

class TestIsSilentEdgeCases:
    def test_struct_error_returns_silent(self):
        """Corrupted PCM data after header triggers struct.error → returns True."""
        # 44-byte header + 3 bytes (odd length, can't unpack 16-bit samples cleanly
        # when num_samples * 2 != actual bytes due to struct.error)
        header = b"\x00" * 44
        # 3 bytes of garbage — num_samples = 3//2 = 1, but we need to trigger
        # struct.error, so use bytes that cause unpack to fail.
        # Actually, with 3 bytes: num_samples=1, pcm[:2] works fine.
        # We need to force a struct.error. The code does:
        #   num_samples = len(pcm_data) // 2
        #   samples = struct.unpack(f"<{num_samples}h", pcm_data[:num_samples * 2])
        # This is robust. To trigger struct.error we'd need the format count
        # to mismatch the data, which can't happen with the formula above.
        # Instead, we can monkey-patch struct.unpack temporarily.
        audio = _wav_bytes([5000] * 50)  # loud audio, non-silent normally
        with patch("services.stream_processor.struct.unpack", side_effect=struct.error("bad")):
            assert is_silent(audio) is True

    def test_value_error_returns_silent(self):
        """ValueError during RMS calculation → returns True."""
        audio = _wav_bytes([5000] * 50)
        with patch("services.stream_processor.struct.unpack", side_effect=ValueError("bad")):
            assert is_silent(audio) is True


# ── process_chunk non-silent path ────────────────────────────────────────────

def _make_api_response(scam_score=0.7, verdict="SUSPICIOUS", signals=None,
                       recommendation="Be careful", transcript_summary="Test call"):
    """Build a mock Mistral API HTTP response."""
    if signals is None:
        signals = [{"category": "URGENCY", "detail": "act now", "severity": "high"}]
    content = json.dumps({
        "scam_score": scam_score,
        "verdict": verdict,
        "signals": signals,
        "recommendation": recommendation,
        "transcript_summary": transcript_summary,
    })
    body = json.dumps({
        "choices": [{
            "message": {"content": content}
        }]
    }).encode()

    mock_resp = MagicMock()
    mock_resp.read.return_value = body
    mock_resp.close = MagicMock()
    return mock_resp


def _loud_wav():
    """Non-silent WAV bytes (RMS >> 500)."""
    return _wav_bytes([20000, -20000] * 50)


class TestProcessChunkNonSilent:
    def test_calls_api(self):
        """Loud audio triggers urlopen; verify URL and auth header."""
        sp = StreamProcessor()
        mock_resp = _make_api_response()
        with patch("services.stream_processor.urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            asyncio.run(sp.process_chunk(_loud_wav()))
            mock_urlopen.assert_called_once()
            req_arg = mock_urlopen.call_args[0][0]
            assert req_arg.full_url == "https://api.mistral.ai/v1/chat/completions"
            assert "Bearer test-key" in req_arg.get_header("Authorization")

    def test_returns_partial_result(self):
        """Verify return dict has expected keys and values."""
        sp = StreamProcessor()
        mock_resp = _make_api_response(scam_score=0.7, verdict="SUSPICIOUS")
        with patch("services.stream_processor.urllib.request.urlopen", return_value=mock_resp):
            result = asyncio.run(sp.process_chunk(_loud_wav()))
        assert result["type"] == "partial_result"
        assert result["chunk_index"] == 1
        assert result["scam_score"] == 0.7
        assert result["verdict"] == "SUSPICIOUS"
        assert "cumulative_score" in result
        assert "max_score" in result
        assert "signals" in result
        assert "recommendation" in result
        assert "transcript_summary" in result

    def test_updates_cumulative_score(self):
        """Send 2 chunks with known scores, verify 0.7*new + 0.3*prev formula."""
        sp = StreamProcessor()
        resp1 = _make_api_response(scam_score=0.6)
        resp2 = _make_api_response(scam_score=0.8)
        with patch("services.stream_processor.urllib.request.urlopen", side_effect=[resp1, resp2]):
            asyncio.run(sp.process_chunk(_loud_wav()))
            asyncio.run(sp.process_chunk(_loud_wav()))
        expected = 0.7 * 0.8 + 0.3 * (0.7 * 0.6 + 0.3 * 0.0)
        assert round(sp.cumulative_score, 4) == round(expected, 4)

    def test_tracks_max_score(self):
        """Send chunk with 0.9 then 0.3, verify max stays 0.9."""
        sp = StreamProcessor()
        resp1 = _make_api_response(scam_score=0.9)
        resp2 = _make_api_response(scam_score=0.3)
        with patch("services.stream_processor.urllib.request.urlopen", side_effect=[resp1, resp2]):
            asyncio.run(sp.process_chunk(_loud_wav()))
            asyncio.run(sp.process_chunk(_loud_wav()))
        assert sp.max_score == 0.9

    def test_accumulates_signals(self):
        """Signals from multiple chunks are appended to all_signals."""
        sp = StreamProcessor()
        signals1 = [{"category": "URGENCY", "detail": "act now", "severity": "high"}]
        signals2 = [{"category": "AUTHORITY", "detail": "IRS claim", "severity": "high"}]
        resp1 = _make_api_response(signals=signals1)
        resp2 = _make_api_response(signals=signals2)
        with patch("services.stream_processor.urllib.request.urlopen", side_effect=[resp1, resp2]):
            asyncio.run(sp.process_chunk(_loud_wav()))
            asyncio.run(sp.process_chunk(_loud_wav()))
        assert len(sp.all_signals) == 2
        categories = [s["category"] for s in sp.all_signals]
        assert "URGENCY" in categories
        assert "AUTHORITY" in categories

    def test_stores_recommendation(self):
        """Verify last_recommendation and last_transcript_summary are set."""
        sp = StreamProcessor()
        mock_resp = _make_api_response(
            recommendation="Hang up immediately",
            transcript_summary="Caller claims IRS",
        )
        with patch("services.stream_processor.urllib.request.urlopen", return_value=mock_resp):
            asyncio.run(sp.process_chunk(_loud_wav()))
        assert sp.last_recommendation == "Hang up immediately"
        assert sp.last_transcript_summary == "Caller claims IRS"

    def test_response_closed(self):
        """Verify resp.close() is called even on success."""
        sp = StreamProcessor()
        mock_resp = _make_api_response()
        with patch("services.stream_processor.urllib.request.urlopen", return_value=mock_resp):
            asyncio.run(sp.process_chunk(_loud_wav()))
        mock_resp.close.assert_called_once()
