"""Logging configuration for the infrastructure layer."""

from __future__ import annotations

from dota_tracker.shared.logger import setup_logger


def setup_logging(log_level: str = "INFO", log_file: str | None = None) -> None:
    """Configure application-wide logging via loguru.

    Sensitive values (API keys, passwords, tokens) are redacted from log
    messages by the shared logger filter.
    """
    setup_logger(level=log_level, log_file=log_file)


__all__ = ["setup_logging"]
