"""HTTP client that delegates URL validation to the validator microservice.

This is the seam that makes web mocking natural in tests: instead of really
calling ``validator-service`` over the network, tests mock this HTTP call.
"""

import os

import httpx


class ValidatorClient:
    """Thin client over the ``validator-service`` ``POST /validate`` endpoint."""

    def __init__(self, base_url: str | None = None, timeout: float = 5.0) -> None:
        self.base_url = (
            base_url or os.getenv("VALIDATOR_URL", "http://validator-service:8001")
        ).rstrip("/")
        self.timeout = timeout

    def validate(self, url: str) -> bool:
        """Return ``True`` only if the URL is well formed *and* reachable.

        Network or service errors are treated as "not valid" so the shortener
        fails closed rather than creating links for unverifiable URLs.
        """
        try:
            response = httpx.post(
                f"{self.base_url}/validate",
                json={"url": url},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError:
            return False

        data = response.json()
        return bool(data.get("valid")) and bool(data.get("reachable"))
