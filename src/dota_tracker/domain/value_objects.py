"""Value objects and identifiers for the domain layer."""

from __future__ import annotations

from enum import StrEnum

from dota_tracker.shared.types import AccountId, HeroId, ItemId, MatchId, PlayerId


class MatchOutcome(StrEnum):
    """Outcome of a match from a team's perspective."""

    RADIANT_WIN = "radiant_win"
    DIRE_WIN = "dire_win"
    UNKNOWN = "unknown"


__all__ = ["AccountId", "HeroId", "ItemId", "MatchId", "MatchOutcome", "PlayerId"]
