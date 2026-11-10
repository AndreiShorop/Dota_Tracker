"""Utility functions for the shared kernel."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypeVar

T = TypeVar("T")


def utcnow() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


def to_datetime(timestamp: int | float | None) -> datetime | None:
    """Convert a Unix timestamp to a UTC datetime.

    Returns None if the timestamp is falsy.
    """
    if timestamp is None:
        return None
    return datetime.fromtimestamp(float(timestamp), tz=UTC)


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide numerator by denominator, returning default on zero division."""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a value to the inclusive range [low, high]."""
    if low > high:
        raise ValueError("low must be <= high")
    return max(low, min(value, high))


def chunk_list(items: list[T], size: int) -> list[list[T]]:  # noqa: UP047
    """Split a list into chunks of the given size."""
    if size <= 0:
        raise ValueError("size must be greater than 0")
    return [items[index : index + size] for index in range(0, len(items), size)]


def format_duration(seconds: int) -> str:
    """Format a duration in seconds as 'H:MM:SS' or 'M:SS'."""
    if seconds < 0:
        raise ValueError("seconds must be non-negative")
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def percentage(part: float, whole: float, decimals: int = 2) -> float:
    """Compute a percentage safely, returning 0.0 when whole is zero."""
    if whole == 0:
        return 0.0
    value = (part / whole) * 100
    return round(value, decimals)
