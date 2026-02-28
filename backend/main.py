from fastapi import FastAPI

app = FastAPI(title="Scam Detector API", version="1.0.0")

@app.get("/")
async def root():
    return {"status": "ok", "message": "Scam Detector API"}
