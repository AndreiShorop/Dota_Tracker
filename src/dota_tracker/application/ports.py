"""Application-layer ports (interfaces) for external capabilities.

Ports express what the application needs without specifying technology.
Infrastructure adapters implement these protocols.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from dota_tracker.domain.value_objects import MatchId
from dota_tracker.shared.types import AccountId

if TYPE_CHECKING:
    from dota_tracker.application.dtos import HeroDTO, ItemDTO, MatchDTO, PlayerDTO


@runtime_checkable
class OpenDotaGateway(Protocol):
    """Gateway to the OpenDota API (driven/secondary port)."""

    def get_player(self, account_id: AccountId) -> PlayerDTO | None:
        """Fetch a player profile by OpenDota/Steam account id."""

    def get_player_recent_matches(self, account_id: AccountId, limit: int = 20) -> list[MatchDTO]:
        """Fetch recent matches for a player, newest first."""

    def get_match(self, match_id: MatchId) -> MatchDTO | None:
        """Fetch a single match by OpenDota match id."""

    def get_heroes(self) -> list[HeroDTO]:
        """Fetch the full hero catalog."""

    def get_items(self) -> list[ItemDTO]:
        """Fetch the full item catalog."""


@runtime_checkable
class UnitOfWork(Protocol):
    """Transaction boundary port used by use cases."""

    def commit(self) -> None:
        """Commit the current unit of work."""

    def rollback(self) -> None:
        """Roll back the current unit of work."""


__all__ = ["OpenDotaGateway", "UnitOfWork"]
