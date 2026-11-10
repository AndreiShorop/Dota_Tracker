"""Low-level OpenDota HTTP client with rate limiting and retry/backoff.

Built on sync ``httpx.Client``. A shared token bucket paces requests to stay
under the OpenDota rate limit; transient errors and 429/5xx responses are
retried with exponential backoff plus jitter.
"""

from __future__ import annotations

import random
import time
from threading import Lock

import httpx
from loguru import logger

from dota_tracker.infrastructure.opendota.exceptions import (
    OpenDotaNotFoundError,
    OpenDotaRateLimitError,
    OpenDotaRequestError,
    OpenDotaUnavailableError,
)

RETRYABLE_SERVER_ERRORS = {500, 502, 503, 504}

BACKOFF_BASE_SECONDS = 0.5
BACKOFF_MAX_SECONDS = 30.0


class TokenBucket:
    """Token bucket limiter that blocks until a permit is available."""

    def __init__(self, rate_per_second: float, capacity: float | None = None) -> None:
        if rate_per_second <= 0:
            raise ValueError("rate_per_second must be positive")
        self._rate = rate_per_second
        self._capacity = capacity if capacity is not None else rate_per_second
        self._tokens = self._capacity
        self._last = time.monotonic()
        self._lock = Lock()

    def acquire(self) -> None:
        """Block until a permit is available, then consume one token."""
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last
                self._last = now
                self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return
                wait = (1.0 - self._tokens) / self._rate
            time.sleep(wait)


class OpenDotaClient:
    """Sync HTTP client for the OpenDota API.

    Args:
        base_url: OpenDota API base URL (trailing slash stripped).
        api_key: Optional API key; sent as the ``api_key`` query param.
        timeout_seconds: Per-request timeout.
        max_retries: Maximum retry attempts for transient failures.
        rate_limit_rpm: Requests per minute budget shared by this client.
        client: Optional pre-built httpx.Client (useful for testing with a
            MockTransport). When omitted, a new client is created.
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str = "",
        timeout_seconds: float = 30.0,
        max_retries: int = 3,
        rate_limit_rpm: int = 60,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._max_retries = max(0, max_retries)
        rate_per_second = rate_limit_rpm / 60.0
        self._limiter = TokenBucket(rate_per_second, capacity=rate_per_second)
        self._client = client or httpx.Client(base_url=self._base_url, timeout=timeout_seconds)

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> OpenDotaClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get(
        self,
        path: str,
        params: dict[str, str | int | float | bool | None] | None = None,
    ) -> httpx.Response:
        """Perform a GET request with rate limiting, retries, and error mapping."""
        return self._request("GET", path, params=params)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str | int | float | bool | None] | None = None,
        json: object | None = None,
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"
        request_params = dict(params or {})
        if self._api_key:
            request_params["api_key"] = self._api_key

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            self._limiter.acquire()
            request = self._client.build_request(method, url, params=request_params, json=json)
            start = time.monotonic()
            try:
                response = self._client.send(request)
            except httpx.TransportError as exc:
                last_error = exc
                logger.warning(
                    "OpenDota request failed (attempt {attempt}): {method} {url} -> {error}",
                    attempt=attempt + 1,
                    method=method,
                    url=url,
                    error=exc,
                )
                if attempt >= self._max_retries:
                    raise OpenDotaUnavailableError(
                        "OpenDota request failed after "
                        f"{self._max_retries + 1} attempts: {method} {url}"
                    ) from exc
                time.sleep(self._backoff(attempt))
                continue

            status = response.status_code
            latency = (time.monotonic() - start) * 1000
            if status == 429:
                last_error = OpenDotaRateLimitError(f"OpenDota rate limit exceeded: {method} {url}")
                logger.warning(
                    "OpenDota rate limited (attempt {attempt}): "
                    "{method} {url} (retry-after={retry_after})",
                    attempt=attempt + 1,
                    method=method,
                    url=url,
                    retry_after=response.headers.get("retry-after"),
                )
                if attempt >= self._max_retries:
                    raise last_error
                retry_after = response.headers.get("retry-after")
                wait = float(retry_after) if retry_after else self._backoff(attempt)
                time.sleep(max(wait, 0.0))
                continue
            if status in RETRYABLE_SERVER_ERRORS:
                last_error = OpenDotaUnavailableError(
                    f"OpenDota server error (attempt {attempt + 1}): {status} {method} {url}"
                )
                logger.warning(
                    "OpenDota server error (attempt {attempt}): {method} {url} -> HTTP {status}",
                    attempt=attempt + 1,
                    method=method,
                    url=url,
                    status=status,
                )
                if attempt >= self._max_retries:
                    raise last_error
                time.sleep(self._backoff(attempt))
                continue
            if 400 <= status < 500:
                if status == 404:
                    raise OpenDotaNotFoundError(f"OpenDota resource not found: {method} {url}")
                raise OpenDotaRequestError(f"OpenDota client error HTTP {status}: {method} {url}")
            logger.debug(
                "OpenDota response: {method} {url} -> HTTP {status} in {latency:.1f}ms",
                method=method,
                url=url,
                status=status,
                latency=latency,
            )
            return response

        if last_error is not None:
            raise last_error
        raise OpenDotaUnavailableError(
            f"OpenDota request failed after {self._max_retries + 1} attempts: {method} {url}"
        )

    @staticmethod
    def _backoff(attempt: int) -> float:
        """Exponential backoff with full jitter, capped at the max delay."""
        delay = min(BACKOFF_MAX_SECONDS, BACKOFF_BASE_SECONDS * (2**attempt))
        return random.uniform(0.0, delay)


__all__ = ["OpenDotaClient", "TokenBucket"]
