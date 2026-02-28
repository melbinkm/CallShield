from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import health

app = FastAPI(title="Scam Detector API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5176"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Scam Detector API"}
