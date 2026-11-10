"""Domain-level exceptions for Dota Tracker."""

from __future__ import annotations

from typing import Any


class DotaTrackerError(Exception):
    """Base exception for all application-specific errors."""

    message: str
    details: dict[str, Any] | None

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation of the error."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(DotaTrackerError):
    """Raised when input validation fails."""


class ConfigurationError(DotaTrackerError):
    """Raised when application configuration is invalid."""


class NetworkError(DotaTrackerError):
    """Raised when a network operation fails."""


class ApplicationTimeoutError(DotaTrackerError):
    """Raised when an operation times out."""


class RateLimitError(DotaTrackerError):
    """Raised when an external API rate limit is exceeded."""


class APIResponseError(DotaTrackerError):
    """Raised when an external API returns an invalid or unexpected response."""


class DatabaseError(DotaTrackerError):
    """Raised when a database operation fails."""


class RepositoryError(DotaTrackerError):
    """Raised when a repository operation fails."""


class NotFoundError(DotaTrackerError):
    """Base exception for missing resources."""


class PlayerNotFoundError(NotFoundError):
    """Raised when a player cannot be found."""


class MatchNotFoundError(NotFoundError):
    """Raised when a match cannot be found."""


class HeroNotFoundError(NotFoundError):
    """Raised when a hero cannot be found."""


class ItemNotFoundError(NotFoundError):
    """Raised when an item cannot be found."""
