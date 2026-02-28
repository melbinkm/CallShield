from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health, analyze, stream

app = FastAPI(title="Scam Detector API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5177"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(stream.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Scam Detector API"}
