import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.audio_analyzer import analyze_audio
from services.text_analyzer import analyze_transcript as analyze_text
from services.response_formatter import parse_analysis_result, build_scam_report
from models.schemas import ScamReport, ErrorResponse, TranscriptRequest
from config import MAX_AUDIO_SIZE_MB

router = APIRouter()

@router.post("/api/analyze/audio", response_model=ScamReport)
async def analyze_audio_endpoint(file: UploadFile = File(...)):
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

    # Call Voxtral audio analysis
    try:
        raw_response = await analyze_audio(audio_bytes)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail={"error": "model_error", "detail": "Audio analysis service temporarily unavailable"},
        )

    # Parse response
    try:
        audio_result = parse_analysis_result(raw_response)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail={"error": "parse_error", "detail": "Failed to process analysis results"},
        )

    # Build and return report
    report = build_scam_report(
        mode="audio",
        audio_result=audio_result,
        start_time=start_time,
    )
    return report

@router.post("/api/analyze/transcript", response_model=ScamReport)
async def analyze_transcript_endpoint(request: TranscriptRequest):
    start_time = time.time()

    transcript = request.transcript.strip()
    if not transcript:
        raise HTTPException(
            status_code=400,
            detail={"error": "transcript_too_long", "detail": "Transcript cannot be empty."},
        )

    # Call Mistral text analysis
    try:
        raw_response = await analyze_text(transcript)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail={"error": "model_error", "detail": "Text analysis service temporarily unavailable"},
        )

    # Parse response
    try:
        text_result = parse_analysis_result(raw_response)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail={"error": "parse_error", "detail": "Failed to process analysis results"},
        )

    # Build and return report
    report = build_scam_report(
        mode="text",
        text_result=text_result,
        start_time=start_time,
    )
    return report
