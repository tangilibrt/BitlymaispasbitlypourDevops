"""Unit tests for the validator HTTP client (SERVICES layer).

These satisfy the "web mock" requirement: the real network call to
``validator-service`` is replaced by a mocked HTTP response (respx).
"""

import httpx
import respx

from app.services.validator_service import ValidatorClient

BASE_URL = "http://validator-service:8001"


@respx.mock
def test_validate_returns_true_when_valid_and_reachable():
    route = respx.post(f"{BASE_URL}/validate").mock(
        return_value=httpx.Response(200, json={"valid": True, "reachable": True})
    )
    client = ValidatorClient(base_url=BASE_URL)

    assert client.validate("https://example.com") is True
    assert route.called
    assert route.calls.last.request.read() == b'{"url": "https://example.com"}'


@respx.mock
def test_validate_false_when_not_reachable():
    respx.post(f"{BASE_URL}/validate").mock(
        return_value=httpx.Response(200, json={"valid": True, "reachable": False})
    )
    client = ValidatorClient(base_url=BASE_URL)
    assert client.validate("https://example.com") is False


@respx.mock
def test_validate_false_on_http_error_status():
    respx.post(f"{BASE_URL}/validate").mock(return_value=httpx.Response(500))
    client = ValidatorClient(base_url=BASE_URL)
    assert client.validate("https://example.com") is False


@respx.mock
def test_validate_false_on_network_error():
    respx.post(f"{BASE_URL}/validate").mock(side_effect=httpx.ConnectError("boom"))
    client = ValidatorClient(base_url=BASE_URL)
    assert client.validate("https://example.com") is False


def test_default_base_url_from_env(monkeypatch):
    monkeypatch.setenv("VALIDATOR_URL", "http://custom:9000/")
    client = ValidatorClient()
    assert client.base_url == "http://custom:9000"
