"""FastAPI endpoints for the shortener service (CONTROLLER layer)."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.data.database import get_session
from app.data.repository import LinkRepository
from app.services.shortener_service import (
    InvalidURLError,
    LinkNotFoundError,
    ShortenerService,
)
from app.services.validator_service import ValidatorClient

router = APIRouter()


class ShortenRequest(BaseModel):
    """Request body for ``POST /shorten``."""

    url: str


def get_service(session: Session = Depends(get_session)) -> ShortenerService:
    """Wire the service with its repository and validator client."""
    repository = LinkRepository(session)
    return ShortenerService(repository, ValidatorClient())


@router.post("/shorten")
def shorten(
    payload: ShortenRequest,
    request: Request,
    service: ShortenerService = Depends(get_service),
):
    """Create a short link for a validated URL."""
    try:
        code = service.create_short_link(payload.url)
    except InvalidURLError as exc:
        raise HTTPException(status_code=400, detail="Invalid or unreachable URL") from exc
    short_url = f"{str(request.base_url).rstrip('/')}/{code}"
    return {"code": code, "short_url": short_url}


@router.get("/stats/{code}")
def stats(code: str, service: ShortenerService = Depends(get_service)):
    """Return the long URL and click count for a code."""
    try:
        link = service.get_stats(code)
    except LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Code not found") from exc
    return {"url": link.url, "clicks": link.clicks}


@router.get("/{code}")
def redirect(code: str, service: ShortenerService = Depends(get_service)):
    """Resolve a code to its URL (302) and increment the click counter."""
    try:
        url = service.resolve(code)
    except LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Code not found") from exc
    return RedirectResponse(url=url, status_code=302)
