"""Canned demo responses for when no Mistral API key is configured."""

from __future__ import annotations

import json
import os
import random
import uuid
from copy import deepcopy
from typing import Dict, List, Optional, Tuple

# ── Load all expected outputs at import time ─────────────────────────────────

_DEMO_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "demo",
    "expected_outputs",
)

_RESPONSES = {}  # type: Dict[str, dict]
for _fname in os.listdir(_DEMO_DIR):
    if _fname.endswith(".json"):
        with open(os.path.join(_DEMO_DIR, _fname)) as _f:
            _RESPONSES[_fname[:-5]] = json.load(_f)

# ── Keyword → response mapping for transcript analysis ──────────────────────

_TRANSCRIPT_KEYWORDS = [  # type: List[Tuple[List[str], str]]
    (["irs", "tax", "arrest"], "irs_scam"),
    (["medicare", "benefits", "press 1"], "medicare_robocall"),
    (["amazon", "suspicious", "charge"], "amazon_scam_robocall"),
    (["warranty", "vehicle", "car"], "warranty_robocall"),
    (["social security", "ssn"], "ssn_fraud_robocall"),
]

# Audio responses — the 5 audio-mode expected outputs
_AUDIO_KEYS = [
    "ssn_fraud_robocall",
    "legal_threat_robocall",
    "amazon_scam_robocall",
    "warranty_robocall",
    "medicare_robocall_audio",
]


def _fresh_copy(response: dict, mode_override: Optional[str] = None) -> dict:
    """Return a deep copy with a fresh UUID and realistic processing time."""
    result = deepcopy(response)
    result["id"] = f"analysis_{uuid.uuid4()}"
    result["processing_time_ms"] = round(random.uniform(800, 3000), 2)
    if mode_override:
        result["mode"] = mode_override
    return result


def _adapt_audio_to_text(response: dict) -> dict:
    """Convert an audio-mode response to text-mode for transcript endpoint."""
    result = _fresh_copy(response, mode_override="text")
    if result.get("audio_analysis") and not result.get("text_analysis"):
        result["text_analysis"] = result.pop("audio_analysis")
    return result


def get_demo_transcript_response(transcript: str) -> dict:
    """Match transcript keywords to a canned response."""
    lower = transcript.lower()
    for keywords, key in _TRANSCRIPT_KEYWORDS:
        if any(kw in lower for kw in keywords):
            resp = _RESPONSES.get(key)
            if resp:
                # If the canned response is audio-mode, adapt it
                if resp.get("mode") == "audio":
                    return _adapt_audio_to_text(resp)
                return _fresh_copy(resp)
    # Default: safe call
    return _fresh_copy(_RESPONSES["safe_call"])


def get_demo_audio_response() -> dict:
    """Random pick from audio-mode canned responses."""
    key = random.choice(_AUDIO_KEYS)
    return _fresh_copy(_RESPONSES[key])


def get_demo_stream_chunks() -> list[dict]:
    """Simulated partial results with escalating scores for streaming demo."""
    return [
        {
            "type": "partial_result",
            "chunk_index": 0,
            "scam_score": 0.15,
            "cumulative_score": 0.15,
            "signals": [],
            "recommendation": "Listening... no threats detected yet.",
        },
        {
            "type": "partial_result",
            "chunk_index": 1,
            "scam_score": 0.45,
            "cumulative_score": 0.30,
            "signals": [
                {"category": "AUTHORITY_IMPERSONATION", "detail": "Caller claims to represent a government agency", "severity": "medium"}
            ],
            "recommendation": "Be cautious — potential authority impersonation detected.",
        },
        {
            "type": "partial_result",
            "chunk_index": 2,
            "scam_score": 0.75,
            "cumulative_score": 0.50,
            "signals": [
                {"category": "AUTHORITY_IMPERSONATION", "detail": "Caller claims to represent a government agency", "severity": "medium"},
                {"category": "URGENCY_TACTICS", "detail": "Threatens immediate action if you don't comply", "severity": "high"},
            ],
            "recommendation": "High risk — caller using urgency tactics and authority impersonation.",
        },
        {
            "type": "partial_result",
            "chunk_index": 3,
            "scam_score": 0.90,
            "cumulative_score": 0.65,
            "signals": [
                {"category": "AUTHORITY_IMPERSONATION", "detail": "Caller claims to represent a government agency", "severity": "medium"},
                {"category": "URGENCY_TACTICS", "detail": "Threatens immediate action if you don't comply", "severity": "high"},
                {"category": "UNUSUAL_PAYMENT", "detail": "Requests payment via gift cards", "severity": "high"},
            ],
            "recommendation": "Hang up immediately. This is very likely a scam.",
        },
    ]


def get_demo_stream_final() -> dict:
    """Final summary result for streaming demo."""
    return {
        "type": "final_result",
        "combined_score": 0.65,
        "verdict": "LIKELY_SCAM",
        "total_chunks": 4,
        "max_score": 0.90,
        "signals": [
            {"category": "AUTHORITY_IMPERSONATION", "detail": "Caller claims to represent a government agency", "severity": "medium"},
            {"category": "URGENCY_TACTICS", "detail": "Threatens immediate action if you don't comply", "severity": "high"},
            {"category": "UNUSUAL_PAYMENT", "detail": "Requests payment via gift cards", "severity": "high"},
        ],
        "transcript_summary": "Caller impersonated a government agency, used urgency tactics and threats, and requested payment via gift cards.",
        "recommendation": "Hang up immediately. Do not provide personal information or make any payments. Report this call to the FTC.",
    }
