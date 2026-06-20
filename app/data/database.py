"""Database engine and session management (DATA layer)."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./shortener.db")

# ``check_same_thread`` is only relevant for SQLite when used across threads
# (e.g. by Uvicorn workers).
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=_connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def init_db() -> None:
    """Create all tables. Safe to call multiple times."""
    # Import models so they are registered on ``Base.metadata`` before create_all.
    from app.data import models  # noqa: F401  pylint: disable=import-outside-toplevel,unused-import

    Base.metadata.create_all(bind=engine)


def get_session():
    """FastAPI dependency that yields a scoped DB session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
