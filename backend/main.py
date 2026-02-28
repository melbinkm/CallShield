from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, analyze, stream

app = FastAPI(title="CallShield API", version="1.0.0")

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
    allow_headers=["Content-Type"],
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(stream.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "CallShield API"}
