from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import uuid

class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class Verdict(str, Enum):
    SAFE = "SAFE"
    SUSPICIOUS = "SUSPICIOUS"
    LIKELY_SCAM = "LIKELY_SCAM"
    SCAM = "SCAM"

class Signal(BaseModel):
    category: str
    detail: str
    severity: Severity

class AnalysisResult(BaseModel):
    scam_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    verdict: Verdict
    signals: list[Signal] = []
    transcript_summary: Optional[str] = None
    recommendation: str

class ScamReport(BaseModel):
    id: str = Field(default_factory=lambda: f"analysis_{uuid.uuid4()}")
    mode: str  # "audio", "text", or "stream"
    audio_analysis: Optional[AnalysisResult] = None
    text_analysis: Optional[AnalysisResult] = None
    combined_score: float = Field(ge=0.0, le=1.0)
    processing_time_ms: float

class TranscriptRequest(BaseModel):
    transcript: str = Field(max_length=10000)

class ErrorResponse(BaseModel):
    error: str
    detail: str
