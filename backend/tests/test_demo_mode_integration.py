"""Integration tests proving routers use demo services when DEMO_MODE = True."""

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from services.demo_responses import (
    get_demo_transcript_response,
    _adapt_audio_to_text,
    _RESPONSES,
)


# ── Health endpoint ──────────────────────────────────────────────────────────


class TestHealthDemoMode:
    def test_health_includes_demo_mode_false(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["demo_mode"] is False

    def test_health_includes_demo_mode_true(self, client):
        with patch("routers.health.DEMO_MODE", True):
            resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["demo_mode"] is True


# ── Transcript endpoint demo short-circuit ───────────────────────────────────


class TestTranscriptDemoMode:
    def test_transcript_demo_returns_canned_response(self, client):
        with patch("routers.analyze.DEMO_MODE", True):
            resp = client.post(
                "/api/analyze/transcript",
                json={"transcript": "This is the IRS calling about your tax debt"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "text"
        assert data["text_analysis"] is not None
        assert data["combined_score"] == 1.0

    def test_transcript_demo_does_not_call_analyzer(self, client):
        with patch("routers.analyze.DEMO_MODE", True), \
             patch("routers.analyze.analyze_text", new_callable=AsyncMock) as mock_analyze:
            resp = client.post(
                "/api/analyze/transcript",
                json={"transcript": "This is the IRS calling about your tax debt"},
            )
        assert resp.status_code == 200
        mock_analyze.assert_not_called()

    def test_transcript_demo_still_validates_input(self, client):
        with patch("routers.analyze.DEMO_MODE", True):
            resp = client.post(
                "/api/analyze/transcript",
                json={"transcript": "   "},
            )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"] == "transcript_empty"


# ── Audio endpoint demo short-circuit ────────────────────────────────────────


class TestAudioDemoMode:
    def test_audio_demo_returns_canned_response(self, client, make_valid_wav):
        wav = make_valid_wav()
        with patch("routers.analyze.DEMO_MODE", True):
            resp = client.post(
                "/api/analyze/audio",
                files={"file": ("test.wav", wav, "audio/wav")},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "audio"
        assert data["audio_analysis"] is not None

    def test_audio_demo_does_not_call_analyzer(self, client, make_valid_wav):
        wav = make_valid_wav()
        with patch("routers.analyze.DEMO_MODE", True), \
             patch("routers.analyze.analyze_audio", new_callable=AsyncMock) as mock_analyze:
            resp = client.post(
                "/api/analyze/audio",
                files={"file": ("test.wav", wav, "audio/wav")},
            )
        assert resp.status_code == 200
        mock_analyze.assert_not_called()

    def test_audio_demo_still_validates_input(self, client):
        with patch("routers.analyze.DEMO_MODE", True):
            resp = client.post(
                "/api/analyze/audio",
                files={"file": ("test.mp3", b"\x00" * 100, "audio/mpeg")},
            )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert detail["error"] == "invalid_file_type"


# ── WebSocket streaming demo path ────────────────────────────────────────────


class TestWebSocketDemoMode:
    def test_ws_demo_returns_partial_results(self, client):
        with patch("routers.stream.DEMO_MODE", True):
            with client.websocket_connect("/ws/stream") as ws:
                data = ws.receive_json()
                assert data["type"] == "connected"

                # Send 2 binary chunks
                ws.send_bytes(b"\x00" * 100)
                r1 = ws.receive_json()
                assert r1["type"] == "partial_result"
                assert r1["chunk_index"] == 0

                ws.send_bytes(b"\x00" * 100)
                r2 = ws.receive_json()
                assert r2["type"] == "partial_result"
                assert r2["chunk_index"] == 1

                # Second chunk should have higher scam_score
                assert r2["scam_score"] > r1["scam_score"]

                # Clean exit
                ws.send_json({"type": "end_stream"})
                ws.receive_json()

    def test_ws_demo_end_stream_returns_final(self, client):
        with patch("routers.stream.DEMO_MODE", True):
            with client.websocket_connect("/ws/stream") as ws:
                ws.receive_json()  # connected

                ws.send_json({"type": "end_stream"})
                data = ws.receive_json()
                assert data["type"] == "final_result"
                assert "verdict" in data
                assert "combined_score" in data
                assert "total_chunks" in data

    def test_ws_demo_does_not_create_processor(self, client):
        with patch("routers.stream.DEMO_MODE", True), \
             patch("routers.stream.StreamProcessor") as mock_cls:
            with client.websocket_connect("/ws/stream") as ws:
                ws.receive_json()  # connected
                ws.send_bytes(b"\x00" * 100)
                ws.receive_json()  # partial
                ws.send_json({"type": "end_stream"})
                ws.receive_json()  # final
        mock_cls.assert_not_called()


# ── _adapt_audio_to_text edge cases ──────────────────────────────────────────


class TestAdaptAudioToText:
    def test_adapt_audio_to_text_moves_analysis_field(self):
        source = _RESPONSES["amazon_scam_robocall"]
        result = _adapt_audio_to_text(source)
        assert "audio_analysis" not in result or result["audio_analysis"] is None
        assert result["text_analysis"] is not None
        assert result["mode"] == "text"
        # Original should be unmodified
        assert source["mode"] == "audio"
        assert source["audio_analysis"] is not None

    def test_transcript_response_unique_ids(self):
        r1 = get_demo_transcript_response("This is the IRS calling")
        r2 = get_demo_transcript_response("This is the IRS calling")
        assert r1["id"] != r2["id"]
