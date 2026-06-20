"""Unit tests for the SERVICES layer (shortener business logic).

The repository and the validator client are mocked so the business logic is
tested in isolation.
"""

from unittest.mock import MagicMock

import pytest

from app.services.shortener_service import (
    InvalidURLError,
    LinkNotFoundError,
    ShortenerService,
    normalize_url,
)


def _service(repo=None, validator=None):
    repo = repo or MagicMock()
    validator = validator or MagicMock()
    return ShortenerService(repo, validator), repo, validator


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("test.fr", "https://test.fr"),
        ("www.test.fr", "https://www.test.fr"),
        ("  example.com/path  ", "https://example.com/path"),
        ("http://test.fr", "http://test.fr"),
        ("https://test.fr", "https://test.fr"),
        ("HTTPS://Test.fr", "HTTPS://Test.fr"),
        ("ftp://files.test.fr", "ftp://files.test.fr"),
        ("", ""),
    ],
)
def test_normalize_url(raw, expected):
    assert normalize_url(raw) == expected


def test_create_short_link_normalizes_schemeless_url():
    repo = MagicMock()
    repo.code_exists.return_value = False
    validator = MagicMock()
    validator.validate.return_value = True
    service, _, _ = _service(repo, validator)

    code = service.create_short_link("www.example.com")

    # The validated and stored URL carries the default scheme.
    validator.validate.assert_called_once_with("https://www.example.com")
    repo.create_link.assert_called_once_with(code, "https://www.example.com")


def test_generate_code_length_and_alphabet():
    service, _, _ = _service()
    code = service.generate_code()
    assert len(code) == 6
    assert code.isalnum()


def test_create_short_link_valid_url():
    repo = MagicMock()
    repo.code_exists.return_value = False
    validator = MagicMock()
    validator.validate.return_value = True
    service, _, _ = _service(repo, validator)

    code = service.create_short_link("https://example.com")

    assert len(code) == 6
    validator.validate.assert_called_once_with("https://example.com")
    repo.create_link.assert_called_once_with(code, "https://example.com")


def test_create_short_link_invalid_url_raises():
    validator = MagicMock()
    validator.validate.return_value = False
    service, repo, _ = _service(validator=validator)

    with pytest.raises(InvalidURLError):
        service.create_short_link("not-a-url")
    repo.create_link.assert_not_called()


def test_create_short_link_handles_collision():
    repo = MagicMock()
    # First generated code already exists, second one is free.
    repo.code_exists.side_effect = [True, False]
    validator = MagicMock()
    validator.validate.return_value = True
    service, _, _ = _service(repo, validator)

    code = service.create_short_link("https://example.com")

    assert repo.code_exists.call_count == 2
    repo.create_link.assert_called_once_with(code, "https://example.com")


def test_resolve_returns_url_and_increments():
    repo = MagicMock()
    repo.get_by_code.return_value = MagicMock(url="https://example.com")
    service, _, _ = _service(repo)

    url = service.resolve("abc123")

    assert url == "https://example.com"
    repo.increment_clicks.assert_called_once_with("abc123")


def test_resolve_missing_raises():
    repo = MagicMock()
    repo.get_by_code.return_value = None
    service, _, _ = _service(repo)

    with pytest.raises(LinkNotFoundError):
        service.resolve("ghost0")
    repo.increment_clicks.assert_not_called()


def test_get_stats_returns_link():
    link = MagicMock(url="https://example.com", clicks=7)
    repo = MagicMock()
    repo.get_by_code.return_value = link
    service, _, _ = _service(repo)

    assert service.get_stats("abc123") is link


def test_get_stats_missing_raises():
    repo = MagicMock()
    repo.get_by_code.return_value = None
    service, _, _ = _service(repo)

    with pytest.raises(LinkNotFoundError):
        service.get_stats("ghost0")
