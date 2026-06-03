from fastapi import FastAPI
from app.config import settings

app = FastAPI(title="TravelKeet Bot", version="0.1.0")

@app.get("/v1/health")
async def health():
    return {"status": "ok"}

