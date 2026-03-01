"""Tests for HTTP API endpoints (routers/analyze.py, routers/health.py, main.py root)."""

import json
import pytest
from unittest.mock import patch, AsyncMock


# ── Root & Health ─────────────────────────────────────────────────────────────

class TestRootEndpoint:
    def test_root_returns_status_ok(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestHealthEndpoint:
    def test_health_returns_ok_with_model_and_version(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "model" in data
        assert "version" in data


# ── Audio Upload ──────────────────────────────────────────────────────────────

VALID_ANALYSIS_JSON = json.dumps({
    "scam_score": 0.5,
    "confidence": 0.8,
    "verdict": "SUSPICIOUS",
    "signals": [{"category": "URGENCY", "detail": "act now", "severity": "medium"}],
    "recommendation": "Be cautious.",
    "transcript_summary": "Test call.",
})


class TestAudioUpload:
    def test_audio_valid_wav(self, client, make_valid_wav):
        wav = make_valid_wav()
        with patch("routers.analyze.analyze_audio", new_callable=AsyncMock, return_value=VALID_ANALYSIS_JSON):
            resp = client.post(
                "/api/analyze/audio",
                files={"file": ("test.wav", wav, "audio/wav")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["mode"] == "audio"
        assert "combined_score" in data
        assert "processing_time_ms" in data
        assert data["audio_analysis"] is not None

    def test_audio_non_wav_filename(self, client):
        resp = client.post(
            "/api/analyze/audio",
            files={"file": ("test.mp3", b"\x00" * 100, "audio/mpeg")},
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"] == "invalid_file_type"

    def test_audio_no_filename(self, client):
        resp = client.post(
            "/api/analyze/audio",
            files={"file": ("", b"\x00" * 100, "audio/wav")},
        )
        # Empty filename is rejected — either by FastAPI validation (422) or handler (400)
        assert resp.status_code in (400, 422)

    def test_audio_oversized(self, client, make_valid_wav):
        wav = make_valid_wav()
        with patch("routers.analyze.MAX_AUDIO_SIZE_MB", 0):
            resp = client.post(
                "/api/analyze/audio",
                files={"file": ("test.wav", wav, "audio/wav")},
            )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"] == "file_too_large"

    def test_audio_invalid_magic_bytes(self, client):
        bad_wav = b"\x00" * 100  # no RIFF/WAVE header
        resp = client.post(
            "/api/analyze/audio",
            files={"file": ("test.wav", bad_wav, "audio/wav")},
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"] == "invalid_file_type"

    def test_audio_analyzer_error(self, client, make_valid_wav):
        wav = make_valid_wav()
        with patch(
            "routers.analyze.analyze_audio",
            new_callable=AsyncMock,
            side_effect=RuntimeError("API down"),
        ):
            resp = client.post(
                "/api/analyze/audio",
                files={"file": ("test.wav", wav, "audio/wav")},
            )
        assert resp.status_code == 502
        detail = resp.json()["detail"]
        assert detail["error"] == "model_error"

    def test_audio_parse_error(self, client, make_valid_wav):
        wav = make_valid_wav()
        with patch(
            "routers.analyze.analyze_audio",
            new_callable=AsyncMock,
            return_value="not valid json {{{",
        ):
            resp = client.post(
                "/api/analyze/audio",
                files={"file": ("test.wav", wav, "audio/wav")},
            )
        assert resp.status_code == 502
        detail = resp.json()["detail"]
        assert detail["error"] == "parse_error"


# ── Transcript ────────────────────────────────────────────────────────────────

class TestTranscriptEndpoint:
    def test_transcript_valid(self, client):
        with patch(
            "routers.analyze.analyze_text",
            new_callable=AsyncMock,
            return_value=VALID_ANALYSIS_JSON,
        ):
            resp = client.post(
                "/api/analyze/transcript",
                json={"transcript": "Hello, this is a test call about your account."},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "text"
        assert "combined_score" in data
        assert data["text_analysis"] is not None

    def test_transcript_empty(self, client):
        resp = client.post("/api/analyze/transcript", json={"transcript": "   "})
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"] == "transcript_empty"

    def test_transcript_too_long(self, client):
        resp = client.post(
            "/api/analyze/transcript",
            json={"transcript": "a" * 10001},
        )
        assert resp.status_code == 422

    def test_transcript_analyzer_error(self, client):
        with patch(
            "routers.analyze.analyze_text",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Model unavailable"),
        ):
            resp = client.post(
                "/api/analyze/transcript",
                json={"transcript": "Test transcript content."},
            )
        assert resp.status_code == 502
        detail = resp.json()["detail"]
        assert detail["error"] == "model_error"

    def test_transcript_parse_error(self, client):
        with patch(
            "routers.analyze.analyze_text",
            new_callable=AsyncMock,
            return_value="broken json }{",
        ):
            resp = client.post(
                "/api/analyze/transcript",
                json={"transcript": "Test transcript content."},
            )
        assert resp.status_code == 502
        detail = resp.json()["detail"]
        assert detail["error"] == "parse_error"

    def test_transcript_exceeds_handler_limit(self, client):
        """Patch MAX_TRANSCRIPT_LENGTH to 5 so an 8-char transcript passes Pydantic but fails handler."""
        with patch("routers.analyze.MAX_TRANSCRIPT_LENGTH", 5), \
             patch("routers.analyze.analyze_text", new_callable=AsyncMock) as mock_analyze:
            resp = client.post(
                "/api/analyze/transcript",
                json={"transcript": "12345678"},  # 8 chars > patched limit of 5
            )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"] == "transcript_too_long"
        mock_analyze.assert_not_called()
