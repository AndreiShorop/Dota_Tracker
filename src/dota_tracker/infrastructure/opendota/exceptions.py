"""OpenDota-specific infrastructure exceptions.

All inherit from the shared domain base so application layers can catch
:class:`dota_tracker.shared.exceptions.DotaTrackerError` without importing
infrastructure details.
"""

from __future__ import annotations

from dota_tracker.shared.exceptions import DotaTrackerError


class OpenDotaError(DotaTrackerError):
    """Base exception for all OpenDota infrastructure errors."""


class OpenDotaRequestError(OpenDotaError):
    """Non-retryable client error (4xx except 429)."""


class OpenDotaNotFoundError(OpenDotaRequestError):
    """The requested OpenDota resource does not exist (HTTP 404)."""


class OpenDotaRateLimitError(OpenDotaError):
    """The OpenDota rate limit was exceeded (HTTP 429)."""


class OpenDotaUnavailableError(OpenDotaError):
    """The OpenDota API is unavailable or retries are exhausted."""


class OpenDotaResponseValidationError(OpenDotaError):
    """An OpenDota response failed schema validation (provider drift)."""


__all__ = [
    "OpenDotaError",
    "OpenDotaNotFoundError",
    "OpenDotaRateLimitError",
    "OpenDotaRequestError",
    "OpenDotaResponseValidationError",
    "OpenDotaUnavailableError",
]
