"""Unit tests for the CONTROLLER layer (FastAPI TestClient, service mocked)."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.controllers.url_controller import get_service
from app.main import app
from app.services.shortener_service import InvalidURLError, LinkNotFoundError


@pytest.fixture
def mock_service():
    service = MagicMock()
    app.dependency_overrides[get_service] = lambda: service
    yield service
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    # follow_redirects disabled so we can assert the 302 status code.
    return TestClient(app, follow_redirects=False)


def test_shorten_returns_code_and_short_url(client, mock_service):
    mock_service.create_short_link.return_value = "abc123"

    response = client.post("/shorten", json={"url": "https://example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == "abc123"
    assert body["short_url"].endswith("/abc123")
    mock_service.create_short_link.assert_called_once_with("https://example.com")


def test_shorten_invalid_url_returns_400(client, mock_service):
    mock_service.create_short_link.side_effect = InvalidURLError("bad")

    response = client.post("/shorten", json={"url": "bad"})

    assert response.status_code == 400


def test_redirect_returns_302(client, mock_service):
    mock_service.resolve.return_value = "https://example.com"

    response = client.get("/abc123")

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com"
    mock_service.resolve.assert_called_once_with("abc123")


def test_redirect_unknown_code_returns_404(client, mock_service):
    mock_service.resolve.side_effect = LinkNotFoundError("ghost0")

    response = client.get("/ghost0")

    assert response.status_code == 404


def test_stats_returns_url_and_clicks(client, mock_service):
    mock_service.get_stats.return_value = MagicMock(url="https://example.com", clicks=42)

    response = client.get("/stats/abc123")

    assert response.status_code == 200
    assert response.json() == {"url": "https://example.com", "clicks": 42}


def test_stats_unknown_code_returns_404(client, mock_service):
    mock_service.get_stats.side_effect = LinkNotFoundError("ghost0")

    response = client.get("/stats/ghost0")

    assert response.status_code == 404


def test_index_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "URL Shortener" in response.text
