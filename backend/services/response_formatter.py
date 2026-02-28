import json
import re
from models.schemas import AnalysisResult, ScamReport, Signal, Verdict, Severity
from typing import Optional
from config import THRESHOLD_SAFE, THRESHOLD_SUSPICIOUS, THRESHOLD_LIKELY_SCAM
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

    # Try finding balanced JSON object (handles nested braces properly)
    def find_balanced_json(text: str) -> Optional[str]:
        """Find first complete JSON object with balanced braces."""
        start = text.find("{")
        if start == -1:
            return None
        
        depth = 0
        for i in range(start, len(text)):
            char = text[i]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i+1]
        return None
    
    json_str = find_balanced_json(raw)
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from response: {raw[:200]}")

def parse_analysis_result(raw: str) -> AnalysisResult:
    """Parse raw model output into a validated AnalysisResult."""
    data = extract_json(raw)

    # Validate verdict against enum values
    valid_verdicts = {v.value for v in Verdict}
    raw_verdict = data.get("verdict", "SAFE")
    if raw_verdict not in valid_verdicts:
        raw_verdict = "SAFE"  # Fallback to safe default

    signals = []
    for s in data.get("signals", []):
        # Validate severity against enum values
        valid_severities = {sev.value for sev in Severity}
        raw_severity = s.get("severity", "medium")
        if raw_severity not in valid_severities:
            raw_severity = "medium"  # Fallback to medium default
        
        signals.append(Signal(
            category=s.get("category", "UNKNOWN"),
            detail=s.get("detail", ""),
            severity=raw_severity,
        ))

    # Clamp scam_score to valid range [0.0, 1.0]
    raw_score = float(data.get("scam_score", 0.0))
    clamped_score = max(0.0, min(1.0, raw_score))
    
    return AnalysisResult(
        scam_score=clamped_score,
        confidence=max(0.0, min(1.0, float(data.get("confidence", 0.5)))),
        verdict=raw_verdict,
        signals=signals,
        transcript_summary=data.get("transcript_summary"),
        recommendation=data.get("recommendation", "No specific recommendation."),
    )

def score_to_verdict(score: float) -> str:
    """Convert a scam score to a verdict string."""
    if score < THRESHOLD_SAFE:
        return "SAFE"
    elif score < THRESHOLD_SUSPICIOUS:
        return "SUSPICIOUS"
    elif score < THRESHOLD_LIKELY_SCAM:
        return "LIKELY_SCAM"
    else:
        return "SCAM"

def build_scam_report(
    mode: str,
    audio_result: Optional[AnalysisResult] = None,
    text_result: Optional[AnalysisResult] = None,
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
