"""Application-wide constants for Dota Tracker."""

from __future__ import annotations

APP_NAME: str = "Dota Tracker"
APP_VERSION: str = "0.1.0"

DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 200

OPENDOTA_DEFAULT_BASE_URL: str = "https://api.opendota.com/api"
OPENDOTA_API_TIMEOUT_SECONDS: float = 30.0
OPENDOTA_MAX_RETRIES: int = 3
OPENDOTA_RATE_LIMIT_RPM: int = 60

DEFAULT_TIMEZONE: str = "UTC"

SUPPORTED_HERO_ROLES: tuple[str, str, str, str, str] = (
    "Carry",
    "Support",
    "Offlane",
    "Mid",
    "Jungle",
)
