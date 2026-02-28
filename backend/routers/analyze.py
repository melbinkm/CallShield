import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from services.audio_analyzer import analyze_audio
from services.response_formatter import parse_analysis_result, build_scam_report
from models.schemas import ScamReport, ErrorResponse
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

    # Call Voxtral audio analysis
    try:
        raw_response = await analyze_audio(audio_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "model_error", "detail": f"Mistral API error: {str(e)}"},
        )

    # Parse response
    try:
        audio_result = parse_analysis_result(raw_response)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={"error": "parse_error", "detail": f"Could not parse model response: {str(e)}"},
        )

    # Build and return report
    report = build_scam_report(
        mode="audio",
        audio_result=audio_result,
        start_time=start_time,
    )
    return report
