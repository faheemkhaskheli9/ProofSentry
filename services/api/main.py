from fastapi import FastAPI
from pydantic import BaseModel

from services.api.sessions import router

app = FastAPI(title="ProofSentry", version="0.1.0")


app.include_router(router)


class Health(BaseModel):
    status: str


@app.get("/healthz", response_model=Health)
def health() -> Health:
    """Process liveness only. This endpoint accepts no submissions."""
    return Health(status="ok")
