import time
import asyncio
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request

logger = logging.getLogger(__name__)
from services.audio_analyzer import analyze_audio
from services.text_analyzer import analyze_transcript as analyze_text
from services.response_formatter import parse_analysis_result, build_scam_report
from models.schemas import ScamReport, ErrorResponse, TranscriptRequest
from config import MAX_AUDIO_SIZE_MB, MAX_TRANSCRIPT_LENGTH, DEMO_MODE
from auth import require_api_key
from rate_limit import limiter
from services.demo_responses import get_demo_audio_response, get_demo_transcript_response

router = APIRouter()

@router.post("/api/analyze/audio", response_model=ScamReport)
@limiter.limit("10/minute")
async def analyze_audio_endpoint(request: Request, file: UploadFile = File(...), _key=Depends(require_api_key)):
    start_time = time.time()

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".wav"):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_file_type", "detail": "Only WAV files are accepted."},
        )

    # Read and validate file size
    audio_bytes = await file.read()
    size_mb = len(audio_bytes) / (1024 * 1024)
    if size_mb > MAX_AUDIO_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail={"error": "file_too_large", "detail": f"File exceeds {MAX_AUDIO_SIZE_MB}MB limit."},
        )

    # Validate WAV magic bytes
    if len(audio_bytes) >= 12 and (audio_bytes[:4] != b'RIFF' or audio_bytes[8:12] != b'WAVE'):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_file_type", "detail": "File is not a valid WAV format."},
        )

    if DEMO_MODE:
        await asyncio.sleep(1.5)
        return get_demo_audio_response()

    # Call Voxtral audio analysis
    try:
        raw_response = await analyze_audio(audio_bytes)
    except Exception as e:
        logger.exception("Audio analysis failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={"error": "model_error", "detail": f"Audio analysis failed: {e}"},
        )

    # Parse response
    try:
        audio_result = parse_analysis_result(raw_response)
    except Exception as e:
        logger.exception("Parse failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={"error": "parse_error", "detail": f"Failed to parse results: {e}"},
        )

    # Conditional second-opinion via Mistral Large when Voxtral score > 0.5
    text_result = None
    if not DEMO_MODE and audio_result.scam_score > 0.5 and audio_result.transcript_summary:
        try:
            raw_text = await analyze_text(audio_result.transcript_summary)
            text_result = parse_analysis_result(raw_text)
        except Exception as e:
            logger.warning("Second-opinion analysis failed (non-fatal): %s", e)

    # Build and return report
    report = build_scam_report(
        mode="audio",
        audio_result=audio_result,
        text_result=text_result,
        start_time=start_time,
    )
    return report

@router.post("/api/analyze/transcript", response_model=ScamReport)
@limiter.limit("20/minute")
async def analyze_transcript_endpoint(request: Request, body: TranscriptRequest, _key=Depends(require_api_key)):
    start_time = time.time()

    transcript = body.transcript.strip()
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail={"error": "transcript_empty", "detail": "Transcript cannot be empty."},
        )
    if len(transcript) > MAX_TRANSCRIPT_LENGTH:
        raise HTTPException(
            status_code=400,
            detail={"error": "transcript_too_long", "detail": f"Transcript exceeds {MAX_TRANSCRIPT_LENGTH} character limit."},
        )

    if DEMO_MODE:
        await asyncio.sleep(1.0)
        return get_demo_transcript_response(transcript)

    # Call Mistral text analysis
    try:
        raw_response = await analyze_text(transcript)
    except Exception as e:
        logger.exception("Text analysis failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={"error": "model_error", "detail": f"Text analysis service temporarily unavailable: {e}"},
        )

    # Parse response
    try:
        text_result = parse_analysis_result(raw_response)
    except Exception as e:
        logger.exception("Text result parsing failed: %s", e)
        raise HTTPException(
            status_code=502,
            detail={"error": "parse_error", "detail": f"Failed to process analysis results: {e}"},
        )

    # Build and return report
    report = build_scam_report(
        mode="text",
        text_result=text_result,
        start_time=start_time,
    )
    return report
