"""Shared pytest fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.data import models  # noqa: F401  ensures tables are registered
from app.data.database import Base


@pytest.fixture
def session():
    """Provide an isolated in-memory SQLite session per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared in-memory DB for the connection
        future=True,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, future=True)
    db = testing_session()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()
