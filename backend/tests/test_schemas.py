"""Tests for models/schemas.py Pydantic model validation."""

import sys
import os
import types

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
sys.modules.setdefault("config", _config)

_mistralai = types.ModuleType("mistralai")
_mistralai.Mistral = lambda **kw: None
sys.modules.setdefault("mistralai", _mistralai)

import pytest
from pydantic import ValidationError
from models.schemas import (
    Verdict,
    Severity,
    Signal,
    AnalysisResult,
    ScamReport,
    TranscriptRequest,
    ErrorResponse,
)


# ── Verdict & Severity Enums ─────────────────────────────────────────────────

class TestVerdictEnum:
    def test_verdict_values(self):
        assert set(v.value for v in Verdict) == {"SAFE", "SUSPICIOUS", "LIKELY_SCAM", "SCAM"}

    def test_severity_values(self):
        assert set(s.value for s in Severity) == {"low", "medium", "high"}

    def test_verdict_string_behavior(self):
        assert Verdict.SAFE == "SAFE"
        assert Verdict.SCAM == "SCAM"


# ── Signal ────────────────────────────────────────────────────────────────────

class TestSignal:
    def test_signal_valid(self):
        s = Signal(category="URGENCY", detail="Act now", severity="high")
        assert s.category == "URGENCY"
        assert s.detail == "Act now"
        assert s.severity == Severity.high

    def test_signal_invalid_severity(self):
        with pytest.raises(ValidationError):
            Signal(category="TEST", detail="d", severity="extreme")


# ── AnalysisResult ────────────────────────────────────────────────────────────

class TestAnalysisResult:
    def test_analysis_result_valid(self):
        ar = AnalysisResult(
            scam_score=0.5,
            confidence=0.8,
            verdict="SUSPICIOUS",
            signals=[],
            recommendation="Be careful.",
        )
        assert ar.scam_score == 0.5
        assert ar.verdict == Verdict.SUSPICIOUS

    def test_analysis_result_score_too_high(self):
        with pytest.raises(ValidationError):
            AnalysisResult(
                scam_score=1.5, confidence=0.8, verdict="SAFE",
                signals=[], recommendation="test",
            )

    def test_analysis_result_score_negative(self):
        with pytest.raises(ValidationError):
            AnalysisResult(
                scam_score=-0.1, confidence=0.8, verdict="SAFE",
                signals=[], recommendation="test",
            )

    def test_analysis_result_confidence_too_high(self):
        with pytest.raises(ValidationError):
            AnalysisResult(
                scam_score=0.5, confidence=1.5, verdict="SAFE",
                signals=[], recommendation="test",
            )

    def test_analysis_result_optional_summary(self):
        ar = AnalysisResult(
            scam_score=0.5, confidence=0.8, verdict="SAFE",
            signals=[], recommendation="test", transcript_summary=None,
        )
        assert ar.transcript_summary is None


# ── ScamReport ────────────────────────────────────────────────────────────────

class TestScamReport:
    def test_scam_report_valid(self):
        r = ScamReport(mode="audio", combined_score=0.5, processing_time_ms=100.0)
        assert r.mode == "audio"
        assert r.combined_score == 0.5

    def test_scam_report_auto_id(self):
        r = ScamReport(mode="audio", combined_score=0.5, processing_time_ms=100.0)
        assert r.id.startswith("analysis_")

    def test_scam_report_score_bounds(self):
        with pytest.raises(ValidationError):
            ScamReport(mode="audio", combined_score=1.5, processing_time_ms=100.0)

    def test_scam_report_optional_analyses(self):
        r = ScamReport(mode="audio", combined_score=0.5, processing_time_ms=100.0)
        assert r.audio_analysis is None
        assert r.text_analysis is None


# ── TranscriptRequest ────────────────────────────────────────────────────────

class TestTranscriptRequest:
    def test_transcript_request_valid(self):
        tr = TranscriptRequest(transcript="Hello, this is a test call.")
        assert tr.transcript == "Hello, this is a test call."

    def test_transcript_request_max_length(self):
        with pytest.raises(ValidationError):
            TranscriptRequest(transcript="a" * 10001)


# ── ErrorResponse ─────────────────────────────────────────────────────────────

class TestErrorResponse:
    def test_error_response_valid(self):
        er = ErrorResponse(error="test_error", detail="Something went wrong")
        assert er.error == "test_error"
        assert er.detail == "Something went wrong"
