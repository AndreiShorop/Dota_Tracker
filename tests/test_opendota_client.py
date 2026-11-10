"""Unit tests for OpenDota client: token bucket, retry, error mapping."""

from __future__ import annotations

import httpx
import pytest

from dota_tracker.infrastructure.opendota.client import OpenDotaClient, TokenBucket
from dota_tracker.infrastructure.opendota.exceptions import (
    OpenDotaNotFoundError,
    OpenDotaRateLimitError,
    OpenDotaRequestError,
    OpenDotaUnavailableError,
)


def test_token_bucket_acquires_permits():
    bucket = TokenBucket(rate_per_second=1000, capacity=10)
    for _ in range(10):
        bucket.acquire()
    bucket.acquire()


def _make_client(handler, *, max_retries: int = 3, rate_limit_rpm: int = 6000) -> OpenDotaClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport, base_url="https://api.opendota.com/api")
    return OpenDotaClient(
        "https://api.opendota.com/api",
        client=http_client,
        max_retries=max_retries,
        rate_limit_rpm=rate_limit_rpm,
    )


def test_get_maps_404_to_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, request=request, json={"error": "not found"})

    client = _make_client(handler)
    with pytest.raises(OpenDotaNotFoundError):
        client.get("/players/999")
    client.close()


def test_get_maps_400_to_request_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, request=request, json={"error": "bad"})

    client = _make_client(handler)
    with pytest.raises(OpenDotaRequestError):
        client.get("/players/999")
    client.close()


def test_get_retries_5xx_then_unavailable():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503, request=request)

    client = _make_client(handler, max_retries=2)
    with pytest.raises(OpenDotaUnavailableError):
        client.get("/matches/1")
    assert attempts == 3  # initial + 2 retries
    client.close()


def test_get_returns_success():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, request=request, json={"account_id": 42})

    client = _make_client(handler)
    response = client.get("/players/42")
    assert response.status_code == 200
    assert response.json()["account_id"] == 42
    client.close()


def test_rate_limit_429_retries_then_raises():
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(429, request=request, headers={"retry-after": "0"})

    client = _make_client(handler, max_retries=1)
    with pytest.raises(OpenDotaRateLimitError):
        client.get("/players/1")
    assert attempts == 2  # initial + 1 retry
    client.close()
