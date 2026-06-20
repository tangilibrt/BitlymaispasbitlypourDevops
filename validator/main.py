"""Entry point for the validator-service FastAPI application."""

from fastapi import FastAPI
from pydantic import BaseModel

from validator.validator_logic import validate_url

app = FastAPI(title="URL Validator", version="1.0.0")


class ValidateRequest(BaseModel):
    """Request body for ``POST /validate``."""

    url: str


@app.get("/health", include_in_schema=False)
def health() -> dict:
    """Liveness probe."""
    return {"status": "ok"}


@app.post("/validate")
def validate(payload: ValidateRequest) -> dict:
    """Return whether the URL is well formed and reachable."""
    valid, reachable = validate_url(payload.url)
    return {"valid": valid, "reachable": reachable}
