"""Shared kernel package for cross-cutting concerns."""

from dota_tracker.shared.constants import (
    APP_NAME,
    APP_VERSION,
)
from dota_tracker.shared.exceptions import (
    APIResponseError,
    ApplicationTimeoutError,
    ConfigurationError,
    DatabaseError,
    DotaTrackerError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    RepositoryError,
    ValidationError,
)
from dota_tracker.shared.logger import setup_logger
from dota_tracker.shared.types import (
    AccountId,
    HeroId,
    ItemId,
    MatchId,
    PlayerId,
)
from dota_tracker.shared.utils import (
    chunk_list,
    clamp,
    format_duration,
    percentage,
    safe_div,
    to_datetime,
    utcnow,
)

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APIResponseError",
    "AccountId",
    "ApplicationTimeoutError",
    "ConfigurationError",
    "DatabaseError",
    "DotaTrackerError",
    "HeroId",
    "ItemId",
    "MatchId",
    "NetworkError",
    "NotFoundError",
    "PlayerId",
    "RateLimitError",
    "RepositoryError",
    "ValidationError",
    "chunk_list",
    "clamp",
    "format_duration",
    "percentage",
    "safe_div",
    "setup_logger",
    "to_datetime",
    "utcnow",
]
