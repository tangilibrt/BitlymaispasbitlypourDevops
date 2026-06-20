"""Entry point for the shortener-service FastAPI application."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.controllers.url_controller import router
from app.data.database import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Create database tables on startup."""
    init_db()
    yield


app = FastAPI(title="URL Shortener", version="1.0.0", lifespan=lifespan)

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the minimal web front-end."""
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


# Mounted last so that explicit routes (``/`` and ``/static``) take precedence
# over the catch-all ``GET /{code}``.
app.include_router(router)
