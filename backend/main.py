from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from rate_limit import limiter
from routers import health, analyze, stream

app = FastAPI(
    title="CallShield API",
    version="1.0.0",
    description=(
        "Real-time phone scam detection powered by Voxtral Mini.\n\n"
        "**Authentication:** Pass your API key via the `X-API-Key` header. "
        "Generate a key with `python scripts/generate_api_key.py --name 'my-app'`.\n\n"
        "When no keys are configured, all endpoints are open (dev mode)."
    ),
)

# Attach rate limiter
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limit_exceeded", "detail": "Too many requests. Please slow down."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://callshield-ui.onrender.com",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(stream.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "CallShield API"}
