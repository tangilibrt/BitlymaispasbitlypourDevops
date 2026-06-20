"""Unit tests for the validator microservice logic.

The outgoing HTTP request to the *target* URL is mocked (respx), so the tests
never depend on the Internet.
"""

import httpx
import respx

from validator.validator_logic import is_well_formed, validate_url

TARGET = "https://example.com"


def test_is_well_formed():
    assert is_well_formed("https://example.com") is True
    assert is_well_formed("http://example.com/path?q=1") is True
    assert is_well_formed("ftp://example.com") is False
    assert is_well_formed("not a url") is False
    assert is_well_formed("") is False


@respx.mock
def test_validate_url_reachable_via_head():
    respx.head(TARGET).mock(return_value=httpx.Response(200))
    assert validate_url(TARGET) == (True, True)


@respx.mock
def test_validate_url_falls_back_to_get():
    respx.head(TARGET).mock(return_value=httpx.Response(405))
    respx.get(TARGET).mock(return_value=httpx.Response(200))
    assert validate_url(TARGET) == (True, True)


@respx.mock
def test_validate_url_not_reachable():
    respx.head(TARGET).mock(return_value=httpx.Response(404))
    respx.get(TARGET).mock(return_value=httpx.Response(404))
    assert validate_url(TARGET) == (True, False)


@respx.mock
def test_validate_url_network_error():
    respx.head(TARGET).mock(side_effect=httpx.ConnectError("down"))
    assert validate_url(TARGET) == (True, False)


def test_validate_url_ill_formed_does_no_network_call():
    # No respx router registered: if a call happened, it would error.
    assert validate_url("not-a-url") == (False, False)
