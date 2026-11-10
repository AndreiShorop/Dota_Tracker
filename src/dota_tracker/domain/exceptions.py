"""Domain exceptions.

Re-exports the shared-kernel exception hierarchy under the domain package so
application and domain code import from a single stable location:
``dota_tracker.domain.exceptions``.
"""

from __future__ import annotations

from dota_tracker.shared.exceptions import (
    APIResponseError,
    ApplicationTimeoutError,
    ConfigurationError,
    DatabaseError,
    DotaTrackerError,
    HeroNotFoundError,
    ItemNotFoundError,
    MatchNotFoundError,
    NetworkError,
    NotFoundError,
    PlayerNotFoundError,
    RateLimitError,
    RepositoryError,
    ValidationError,
)

__all__ = [
    "APIResponseError",
    "ApplicationTimeoutError",
    "ConfigurationError",
    "DatabaseError",
    "DotaTrackerError",
    "HeroNotFoundError",
    "ItemNotFoundError",
    "MatchNotFoundError",
    "NetworkError",
    "NotFoundError",
    "PlayerNotFoundError",
    "RateLimitError",
    "RepositoryError",
    "ValidationError",
]
