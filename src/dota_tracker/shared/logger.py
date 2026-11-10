"""Logger setup for the shared kernel."""

from __future__ import annotations

import re
import sys
from typing import Any

from loguru import logger

__all__ = ["logger", "setup_logger"]

_SENSITIVE_PATTERN = re.compile(r"(?i)\b(api[_-]?key|password|token|secret)\b\s*[:=]\s*([^\s,;]+)")


def _redact_sensitive(record: Any) -> bool:
    """Redact sensitive values from log messages in-place.

    Returns True to allow the record to be logged.
    """
    message = record.get("message") if isinstance(record, dict) else None
    if isinstance(message, str):
        record["message"] = _SENSITIVE_PATTERN.sub(r"\1=<redacted>", message)
    return True


def setup_logger(level: str = "INFO", log_file: str | None = None) -> None:
    """Configure the application logger.

    Args:
        level: Minimum log level for sinks.
        log_file: Optional path to a log file. When provided, logs are also
            written to this file with rotation.
    """
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=log_format,
        filter=_redact_sensitive,
    )

    if log_file:
        logger.add(
            log_file,
            level=level,
            format=log_format,
            filter=_redact_sensitive,
            rotation="10 MB",
        )
