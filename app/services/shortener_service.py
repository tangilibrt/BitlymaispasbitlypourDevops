"""Business logic for creating, resolving and counting short links (SERVICES)."""

import re
import secrets
import string

from app.data.models import Link
from app.data.repository import LinkRepository
from app.services.validator_service import ValidatorClient

# base62 alphabet for short codes.
ALPHABET = string.ascii_letters + string.digits
CODE_LENGTH = 6
MAX_COLLISION_RETRIES = 10

# Matches an explicit URI scheme such as "http://", "https://" or "ftp://".
_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://")


def normalize_url(url: str) -> str:
    """Add a default ``https://`` scheme when the user omits it.

    Accepts inputs like ``test.fr``, ``www.test.fr`` or ``http://test.fr`` and
    returns a fully-qualified URL. An existing scheme (even non-http, so the
    validator can reject it properly) is left untouched.
    """
    url = url.strip()
    if url and not _SCHEME_RE.match(url):
        url = f"https://{url}"
    return url


class InvalidURLError(Exception):
    """Raised when the validator rejects a URL."""


class LinkNotFoundError(Exception):
    """Raised when a short code has no matching link."""


class ShortenerService:
    """Coordinates validation, code generation and persistence."""

    def __init__(self, repository: LinkRepository, validator: ValidatorClient) -> None:
        self.repository = repository
        self.validator = validator

    def generate_code(self, length: int = CODE_LENGTH) -> str:
        """Return a random base62 code of the given length."""
        return "".join(secrets.choice(ALPHABET) for _ in range(length))

    def _unique_code(self) -> str:
        """Generate a code that is not already used, handling collisions."""
        for _ in range(MAX_COLLISION_RETRIES):
            code = self.generate_code()
            if not self.repository.code_exists(code):
                return code
        raise RuntimeError("Unable to generate a unique code after several retries")

    def create_short_link(self, url: str) -> str:
        """Normalize, validate, then create and persist a new short link."""
        url = normalize_url(url)
        if not self.validator.validate(url):
            raise InvalidURLError(url)
        code = self._unique_code()
        self.repository.create_link(code, url)
        return code

    def resolve(self, code: str) -> str:
        """Return the long URL for ``code`` and count the click."""
        link = self.repository.get_by_code(code)
        if link is None:
            raise LinkNotFoundError(code)
        self.repository.increment_clicks(code)
        return link.url

    def get_stats(self, code: str) -> Link:
        """Return the :class:`Link` (url + clicks) for ``code``."""
        link = self.repository.get_by_code(code)
        if link is None:
            raise LinkNotFoundError(code)
        return link
