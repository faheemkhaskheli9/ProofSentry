from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="ProofSentry", version="0.1.0")


class Health(BaseModel):
    status: str


@app.get("/healthz", response_model=Health)
def health() -> Health:
    """Process liveness only. This endpoint accepts no submissions."""
    return Health(status="ok")
