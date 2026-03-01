"""Tests for services/response_formatter.py pure functions."""

import json
import sys
import os
import pytest

# Allow imports from backend/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Stub config before importing response_formatter (avoids needing .env / Mistral key)
import types

_config = types.ModuleType("config")
_config.MISTRAL_API_KEY = "test-key"
_config.AUDIO_MODEL = "voxtral-mini-latest"
_config.TEXT_MODEL = "mistral-large-latest"
_config.MAX_AUDIO_SIZE_MB = 25
_config.MAX_TRANSCRIPT_LENGTH = 10000
_config.THRESHOLD_SAFE = 0.30
_config.THRESHOLD_SUSPICIOUS = 0.60
_config.THRESHOLD_LIKELY_SCAM = 0.85
sys.modules["config"] = _config

# Stub mistralai so importing config doesn't blow up
_mistralai = types.ModuleType("mistralai")
_mistralai.Mistral = lambda **kw: None
sys.modules["mistralai"] = _mistralai

from services.response_formatter import (
    extract_json,
    score_to_verdict,
    parse_analysis_result,
    build_scam_report,
)
from models.schemas import AnalysisResult, Verdict


# ── extract_json ──────────────────────────────────────────────────────────────

class TestExtractJson:
    def test_direct_parse(self):
        raw = '{"scam_score": 0.5, "verdict": "SAFE"}'
        assert extract_json(raw) == {"scam_score": 0.5, "verdict": "SAFE"}

    def test_markdown_fences(self):
        raw = 'Here is the result:\n```json\n{"key": "value"}\n```'
        assert extract_json(raw) == {"key": "value"}

    def test_balanced_braces(self):
        raw = 'Some preamble {"a": {"b": 1}} trailing'
        result = extract_json(raw)
        assert result == {"a": {"b": 1}}

    def test_nested_objects(self):
        obj = {"outer": {"inner": {"deep": [1, 2, 3]}}}
        raw = f"prefix {json.dumps(obj)} suffix"
        assert extract_json(raw) == obj

    def test_no_json_raises_value_error(self):
        with pytest.raises(ValueError, match="Could not extract JSON"):
            extract_json("no json here at all")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            extract_json("")

    def test_markdown_fence_invalid_json_falls_through(self):
        """Markdown fence matches but JSON inside is invalid → falls through to balanced brace."""
        # Valid JSON appears before the fence so find_balanced_json hits it first
        raw = 'Some text {"key": "val"} and ```json\n{not valid json}\n```'
        result = extract_json(raw)
        assert result == {"key": "val"}

    def test_balanced_braces_invalid_json_raises(self):
        """Balanced braces found but json.loads fails → raises ValueError."""
        raw = "prefix {not: valid: json} suffix"
        with pytest.raises(ValueError, match="Could not extract JSON"):
            extract_json(raw)


# ── score_to_verdict ──────────────────────────────────────────────────────────

class TestScoreToVerdict:
    @pytest.mark.parametrize("score,expected", [
        (0.00, "SAFE"),
        (0.29, "SAFE"),
        (0.30, "SUSPICIOUS"),
        (0.59, "SUSPICIOUS"),
        (0.60, "LIKELY_SCAM"),
        (0.84, "LIKELY_SCAM"),
        (0.85, "SCAM"),
        (1.00, "SCAM"),
    ])
    def test_boundary_values(self, score, expected):
        assert score_to_verdict(score) == expected


# ── parse_analysis_result ─────────────────────────────────────────────────────

class TestParseAnalysisResult:
    def _make_raw(self, **overrides):
        base = {
            "scam_score": 0.5,
            "confidence": 0.8,
            "verdict": "SUSPICIOUS",
            "signals": [],
            "recommendation": "Be careful.",
        }
        base.update(overrides)
        return json.dumps(base)

    def test_score_clamped_high(self):
        result = parse_analysis_result(self._make_raw(scam_score=1.5))
        assert result.scam_score == 1.0

    def test_score_clamped_low(self):
        result = parse_analysis_result(self._make_raw(scam_score=-0.3))
        assert result.scam_score == 0.0

    def test_invalid_verdict_defaults_safe(self):
        result = parse_analysis_result(self._make_raw(verdict="BOGUS"))
        assert result.verdict == Verdict.SAFE

    def test_invalid_severity_defaults_medium(self):
        raw = self._make_raw(signals=[
            {"category": "TEST", "detail": "d", "severity": "extreme"}
        ])
        result = parse_analysis_result(raw)
        assert result.signals[0].severity.value == "medium"

    def test_valid_parse(self):
        raw = self._make_raw(
            scam_score=0.7,
            verdict="LIKELY_SCAM",
            signals=[{"category": "URGENCY", "detail": "act now", "severity": "high"}],
        )
        result = parse_analysis_result(raw)
        assert result.scam_score == 0.7
        assert result.verdict == Verdict.LIKELY_SCAM
        assert len(result.signals) == 1

    def test_missing_recommendation_uses_default(self):
        raw = json.dumps({
            "scam_score": 0.5, "confidence": 0.8,
            "verdict": "SAFE", "signals": [],
        })
        result = parse_analysis_result(raw)
        assert result.recommendation == "No specific recommendation."

    def test_missing_verdict_defaults_safe(self):
        raw = json.dumps({
            "scam_score": 0.5, "confidence": 0.8,
            "signals": [], "recommendation": "test",
        })
        result = parse_analysis_result(raw)
        assert result.verdict == Verdict.SAFE

    def test_confidence_clamped_high(self):
        result = parse_analysis_result(self._make_raw(confidence=1.5))
        assert result.confidence == 1.0

    def test_confidence_clamped_low(self):
        result = parse_analysis_result(self._make_raw(confidence=-0.5))
        assert result.confidence == 0.0

    def test_empty_signals_array(self):
        result = parse_analysis_result(self._make_raw(signals=[]))
        assert result.signals == []

    def test_signal_missing_fields_uses_defaults(self):
        raw = self._make_raw(signals=[{"category": "TEST"}])
        result = parse_analysis_result(raw)
        assert result.signals[0].category == "TEST"
        assert result.signals[0].detail == ""


# ── build_scam_report ─────────────────────────────────────────────────────────

def _make_result(score: float) -> AnalysisResult:
    return AnalysisResult(
        scam_score=score,
        confidence=0.9,
        verdict="SAFE",
        signals=[],
        recommendation="test",
    )


class TestBuildScamReport:
    def test_combined_weights(self):
        report = build_scam_report("audio", _make_result(0.8), _make_result(0.6))
        expected = round(0.8 * 0.6 + 0.6 * 0.4, 4)
        assert report.combined_score == expected

    def test_audio_only(self):
        report = build_scam_report("audio", audio_result=_make_result(0.75))
        assert report.combined_score == 0.75

    def test_text_only(self):
        report = build_scam_report("text", text_result=_make_result(0.3))
        assert report.combined_score == 0.3

    def test_no_results_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            build_scam_report("audio")

    def test_four_decimal_rounding(self):
        report = build_scam_report("audio", _make_result(0.123456), _make_result(0.654321))
        # 0.123456*0.6 + 0.654321*0.4 = 0.0740736 + 0.2617284 = 0.335802
        assert report.combined_score == round(0.123456 * 0.6 + 0.654321 * 0.4, 4)

    def test_mode_string_preserved(self):
        report = build_scam_report("stream", audio_result=_make_result(0.5))
        assert report.mode == "stream"

    def test_report_has_unique_id(self):
        r1 = build_scam_report("audio", audio_result=_make_result(0.5))
        r2 = build_scam_report("audio", audio_result=_make_result(0.5))
        assert r1.id != r2.id
