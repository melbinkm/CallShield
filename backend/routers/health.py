from fastapi import APIRouter
from config import DEMO_MODE

router = APIRouter()

@router.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "model": "voxtral-mini-latest",
        "version": "1.0.0",
        "demo_mode": DEMO_MODE,
    }
