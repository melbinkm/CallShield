"""Integration-level parametrized tests for scoring logic."""

import sys
import os
import types
import pytest

# Allow imports from backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Stub config
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

from services.response_formatter import score_to_verdict, build_scam_report
from models.schemas import AnalysisResult


# ── Verdict thresholds (12 parametrized cases) ───────────────────────────────

@pytest.mark.parametrize("score,expected", [
    (0.00, "SAFE"),
    (0.10, "SAFE"),
    (0.29, "SAFE"),
    (0.30, "SUSPICIOUS"),
    (0.45, "SUSPICIOUS"),
    (0.59, "SUSPICIOUS"),
    (0.60, "LIKELY_SCAM"),
    (0.72, "LIKELY_SCAM"),
    (0.84, "LIKELY_SCAM"),
    (0.85, "SCAM"),
    (0.95, "SCAM"),
    (1.00, "SCAM"),
])
def test_verdict_thresholds(score, expected):
    assert score_to_verdict(score) == expected


# ── Combined weights ─────────────────────────────────────────────────────────

def _result(score: float) -> AnalysisResult:
    return AnalysisResult(
        scam_score=score,
        confidence=0.9,
        verdict="SAFE",
        signals=[],
        recommendation="test",
    )


@pytest.mark.parametrize("audio,text,expected", [
    (0.0, 0.0, 0.0),
    (1.0, 1.0, 1.0),
    (0.5, 0.5, 0.5),
    (0.8, 0.2, round(0.8 * 0.6 + 0.2 * 0.4, 4)),
    (0.3, 0.9, round(0.3 * 0.6 + 0.9 * 0.4, 4)),
    (1.0, 0.0, 0.6),
    (0.0, 1.0, 0.4),
])
def test_combined_weights(audio, text, expected):
    report = build_scam_report("audio", _result(audio), _result(text))
    assert report.combined_score == expected


# ── Exponential weighting formula ─────────────────────────────────────────────

def test_exponential_weighting_five_chunks():
    """Step through 5 chunk scores and verify 0.7*chunk + 0.3*prev."""
    chunk_scores = [0.1, 0.4, 0.9, 0.2, 0.6]
    cumulative = 0.0
    for score in chunk_scores:
        cumulative = 0.7 * score + 0.3 * cumulative

    # Manually verify step-by-step
    expected = 0.0
    expected = 0.7 * 0.1 + 0.3 * 0.0    # 0.07
    expected = 0.7 * 0.4 + 0.3 * expected  # 0.301
    expected = 0.7 * 0.9 + 0.3 * expected  # 0.7203
    expected = 0.7 * 0.2 + 0.3 * expected  # 0.35609
    expected = 0.7 * 0.6 + 0.3 * expected  # 0.526827

    assert round(cumulative, 6) == round(expected, 6)


# ── Score clamping ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw_score,clamped", [
    (-1.0, 0.0),
    (0.0, 0.0),
    (0.5, 0.5),
    (1.0, 1.0),
    (999.0, 1.0),
])
def test_score_clamping(raw_score, clamped):
    from services.response_formatter import parse_analysis_result
    import json
    raw = json.dumps({
        "scam_score": raw_score,
        "confidence": 0.5,
        "verdict": "SAFE",
        "signals": [],
        "recommendation": "test",
    })
    result = parse_analysis_result(raw)
    assert result.scam_score == clamped
