"""Tests for the demo response service."""

import sys
import os

# Ensure backend is on sys.path and config stub is loaded
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.demo_responses import (
    get_demo_transcript_response,
    get_demo_audio_response,
    get_demo_stream_chunks,
    get_demo_stream_final,
)


# ── Transcript keyword matching ──────────────────────────────────────────────

def test_transcript_irs_keywords():
    resp = get_demo_transcript_response("This is the IRS calling about your tax debt")
    assert resp["combined_score"] == 1.0
    assert resp["mode"] == "text"
    assert resp["text_analysis"]["verdict"] == "SCAM"


def test_transcript_medicare_keywords():
    resp = get_demo_transcript_response("Important message about your Medicare benefits")
    assert resp["text_analysis"]["verdict"] == "LIKELY_SCAM"
    assert resp["mode"] == "text"


def test_transcript_safe_default():
    resp = get_demo_transcript_response("Hey, want to grab lunch tomorrow?")
    assert resp["combined_score"] == 0.0
    assert resp["text_analysis"]["verdict"] == "SAFE"


def test_transcript_amazon_keywords():
    resp = get_demo_transcript_response("Amazon detected a suspicious charge on your account")
    assert resp["combined_score"] > 0.5
    assert resp["mode"] == "text"
    # Should be adapted from audio to text mode
    assert resp["text_analysis"] is not None


def test_transcript_warranty_keywords():
    resp = get_demo_transcript_response("Your vehicle warranty is about to expire")
    assert resp["combined_score"] > 0.4
    assert resp["mode"] == "text"
    assert resp["text_analysis"] is not None


def test_transcript_ssn_keywords():
    resp = get_demo_transcript_response("Your social security number has been suspended")
    assert resp["combined_score"] > 0.5
    assert resp["mode"] == "text"
    assert resp["text_analysis"] is not None


# ── Audio response ───────────────────────────────────────────────────────────

def test_audio_response_is_valid():
    resp = get_demo_audio_response()
    assert resp["mode"] == "audio"
    assert resp["audio_analysis"] is not None
    assert "combined_score" in resp
    assert "id" in resp
    assert "processing_time_ms" in resp


def test_audio_response_has_unique_id():
    r1 = get_demo_audio_response()
    r2 = get_demo_audio_response()
    assert r1["id"] != r2["id"]


# ── Streaming chunks ────────────────────────────────────────────────────────

def test_stream_chunks_format():
    chunks = get_demo_stream_chunks()
    assert len(chunks) >= 3
    scores = [c["scam_score"] for c in chunks]
    # Scores should be escalating
    assert scores == sorted(scores)
    for chunk in chunks:
        assert chunk["type"] == "partial_result"
        assert "chunk_index" in chunk
        assert "cumulative_score" in chunk
        assert "signals" in chunk
        assert "recommendation" in chunk


def test_stream_final_format():
    final = get_demo_stream_final()
    assert final["type"] == "final_result"
    assert "combined_score" in final
    assert "verdict" in final
    assert "total_chunks" in final
    assert "max_score" in final
    assert "signals" in final
    assert "recommendation" in final


# ── All responses have required fields ───────────────────────────────────────

def test_all_responses_have_required_fields():
    """Every transcript/audio response must have id, mode, combined_score, processing_time_ms."""
    required = {"id", "mode", "combined_score", "processing_time_ms"}
    responses = [
        get_demo_transcript_response("IRS tax"),
        get_demo_transcript_response("just a normal call"),
        get_demo_audio_response(),
    ]
    for resp in responses:
        missing = required - set(resp.keys())
        assert not missing, f"Missing fields: {missing} in response with id={resp.get('id')}"
