import json
import re
from models.schemas import AnalysisResult, ScamReport, Signal, Verdict, Severity
import time
import uuid

def extract_json(raw: str) -> dict:
    """Extract JSON from model response, handling markdown fences and extra text."""
    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fences
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding first JSON object in the text
    brace_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from response: {raw[:200]}")

def parse_analysis_result(raw: str) -> AnalysisResult:
    """Parse raw model output into a validated AnalysisResult."""
    data = extract_json(raw)

    signals = []
    for s in data.get("signals", []):
        signals.append(Signal(
            category=s.get("category", "UNKNOWN"),
            detail=s.get("detail", ""),
            severity=s.get("severity", "medium"),
        ))

    return AnalysisResult(
        scam_score=float(data.get("scam_score", 0.0)),
        confidence=float(data.get("confidence", 0.5)),
        verdict=data.get("verdict", "SAFE"),
        signals=signals,
        transcript_summary=data.get("transcript_summary"),
        recommendation=data.get("recommendation", "No specific recommendation."),
    )

def build_scam_report(
    mode: str,
    audio_result: AnalysisResult | None = None,
    text_result: AnalysisResult | None = None,
    start_time: float = 0.0,
) -> ScamReport:
    """Build a unified ScamReport from one or both analysis results."""
    # Calculate combined score
    if audio_result and text_result:
        combined = audio_result.scam_score * 0.6 + text_result.scam_score * 0.4
    elif audio_result:
        combined = audio_result.scam_score
    elif text_result:
        combined = text_result.scam_score
    else:
        raise ValueError("At least one analysis result is required")

    elapsed_ms = (time.time() - start_time) * 1000

    return ScamReport(
        id=f"analysis_{uuid.uuid4()}",
        mode=mode,
        audio_analysis=audio_result,
        text_analysis=text_result,
        combined_score=round(combined, 4),
        processing_time_ms=round(elapsed_ms, 2),
    )
