"""URL validation logic for the validator microservice."""

from urllib.parse import urlparse

import httpx

_TIMEOUT = 5.0


def is_well_formed(url: str) -> bool:
    """Return whether ``url`` has an http(s) scheme and a network location."""
    try:
        parsed = urlparse(url)
    except (ValueError, TypeError):
        return False
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def is_reachable(url: str) -> bool:
    """Return whether ``url`` answers an HTTP request with a < 400 status.

    Tries a cheap HEAD first, then falls back to GET (many servers do not
    implement HEAD correctly).
    """
    try:
        response = httpx.head(url, timeout=_TIMEOUT, follow_redirects=True)
        if response.status_code >= 400:
            response = httpx.get(url, timeout=_TIMEOUT, follow_redirects=True)
        return response.status_code < 400
    except httpx.HTTPError:
        return False


def validate_url(url: str) -> tuple[bool, bool]:
    """Return ``(valid, reachable)`` for ``url``.

    An ill-formed URL is reported as ``(False, False)`` and never triggers a
    network call.
    """
    if not is_well_formed(url):
        return False, False
    return True, is_reachable(url)
