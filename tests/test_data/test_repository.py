"""Unit tests for the DATA layer (repository on in-memory SQLite)."""

from app.data.repository import LinkRepository


def test_create_and_get_link(session):
    repo = LinkRepository(session)

    created = repo.create_link("abc123", "https://example.com")

    assert created.id is not None
    assert created.clicks == 0
    fetched = repo.get_by_code("abc123")
    assert fetched is not None
    assert fetched.url == "https://example.com"


def test_get_by_code_missing_returns_none(session):
    repo = LinkRepository(session)
    assert repo.get_by_code("nope00") is None


def test_code_exists(session):
    repo = LinkRepository(session)
    repo.create_link("dup123", "https://example.com")

    assert repo.code_exists("dup123") is True
    assert repo.code_exists("free00") is False


def test_increment_clicks_is_atomic_and_counts(session):
    repo = LinkRepository(session)
    repo.create_link("clk001", "https://example.com")

    for _ in range(3):
        affected = repo.increment_clicks("clk001")
        assert affected == 1

    assert repo.get_by_code("clk001").clicks == 3


def test_increment_clicks_missing_returns_zero(session):
    repo = LinkRepository(session)
    assert repo.increment_clicks("ghost0") == 0
