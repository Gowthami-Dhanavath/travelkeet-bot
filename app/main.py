from fastapi import FastAPI

app = FastAPI(title="TravelKeet API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "TravelKeet API running"}

@app.get("/v1/health")
def health():
    return {"status": "ok"}