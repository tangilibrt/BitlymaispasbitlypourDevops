"""Unit tests for the validator microservice endpoint (CONTROLLER)."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from validator.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("validator.main.validate_url", return_value=(True, True))
def test_validate_endpoint_valid(mock_validate):
    response = client.post("/validate", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json() == {"valid": True, "reachable": True}
    mock_validate.assert_called_once_with("https://example.com")


@patch("validator.main.validate_url", return_value=(False, False))
def test_validate_endpoint_invalid(_mock_validate):
    response = client.post("/validate", json={"url": "nope"})

    assert response.status_code == 200
    assert response.json() == {"valid": False, "reachable": False}
