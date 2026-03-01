"""Tests for WebSocket streaming endpoint (routers/stream.py)."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestWebSocketStream:
    def test_ws_connect_receives_connected(self, client):
        with client.websocket_connect("/ws/stream") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            # Clean exit so server breaks its receive loop
            ws.send_json({"type": "end_stream"})
            ws.receive_json()

    def test_ws_end_stream_returns_final(self, client):
        with client.websocket_connect("/ws/stream") as ws:
            data = ws.receive_json()
            assert data["type"] == "connected"
            ws.send_json({"type": "end_stream"})
            data = ws.receive_json()
            assert data["type"] == "final_result"
            assert "combined_score" in data
            assert "verdict" in data

    def test_ws_chunk_too_large(self, client):
        with client.websocket_connect("/ws/stream") as ws:
            ws.receive_json()  # connected
            ws.send_bytes(b"\x00" * (512 * 1024 + 1))
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "too large" in data["detail"]
            # Clean exit
            ws.send_json({"type": "end_stream"})
            ws.receive_json()

    def test_ws_silent_chunk(self, client, make_valid_wav):
        silent_wav = make_valid_wav()  # all-zero PCM = silent
        with client.websocket_connect("/ws/stream") as ws:
            ws.receive_json()  # connected
            ws.send_bytes(silent_wav)
            data = ws.receive_json()
            assert data["type"] == "partial_result"
            assert data["verdict"] == "SAFE"
            assert data["scam_score"] == 0.0
            # Clean exit
            ws.send_json({"type": "end_stream"})
            ws.receive_json()

    def test_ws_invalid_json_text(self, client):
        with client.websocket_connect("/ws/stream") as ws:
            ws.receive_json()  # connected
            ws.send_text("not valid json at all")
            # Connection stays open — verify by sending end_stream
            ws.send_json({"type": "end_stream"})
            data = ws.receive_json()
            assert data["type"] == "final_result"

    def test_ws_process_chunk_error(self, client):
        mock_processor = MagicMock()
        mock_processor.process_chunk = AsyncMock(
            side_effect=RuntimeError("API error")
        )
        mock_processor.get_final_result.return_value = {
            "type": "final_result",
            "total_chunks": 0,
            "combined_score": 0.0,
            "max_score": 0.0,
            "verdict": "SAFE",
            "signals": [],
            "recommendation": "",
            "transcript_summary": "",
        }

        with patch("routers.stream.StreamProcessor", return_value=mock_processor):
            with client.websocket_connect("/ws/stream") as ws:
                ws.receive_json()  # connected
                ws.send_bytes(b"\x00" * 100)
                data = ws.receive_json()
                assert data["type"] == "error"
                assert "API error" in data["detail"]
                # Clean exit: send end_stream so server breaks the loop
                ws.send_json({"type": "end_stream"})
                final = ws.receive_json()
                assert final["type"] == "final_result"

    def test_ws_timeout(self, client):
        """When no data arrives within timeout, server sends error and closes."""
        original_wait_for = asyncio.wait_for

        async def mock_wait_for(coro, *, timeout=None):
            # The handler calls wait_for(ws.receive(), timeout=30.0)
            # Raise TimeoutError to simulate no data received
            if timeout == 30.0:
                # Cancel the pending coroutine to avoid warnings
                coro.close()
                raise asyncio.TimeoutError()
            return await original_wait_for(coro, timeout=timeout)

        with patch("routers.stream.asyncio.wait_for", side_effect=mock_wait_for):
            with client.websocket_connect("/ws/stream") as ws:
                data = ws.receive_json()  # connected
                assert data["type"] == "connected"
                # The next receive loop iteration will hit the timeout
                data = ws.receive_json()
                assert data["type"] == "error"
                assert "timeout" in data["detail"].lower()
