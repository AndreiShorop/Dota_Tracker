"""Application-layer ports (interfaces) for external capabilities.

Ports express what the application needs without specifying technology.
Infrastructure adapters implement these protocols.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from dota_tracker.domain.value_objects import MatchId
from dota_tracker.shared.types import AccountId

if TYPE_CHECKING:
    from dota_tracker.application.dtos import (
        DashboardPlayer,
        HeroDTO,
        ItemDTO,
        MatchDetail,
        MatchDTO,
        PlayerDashboard,
        PlayerDTO,
    )


class DashboardReader(Protocol):
    """Read stored dashboard projections without exposing persistence types."""

    def list_players(self) -> list[DashboardPlayer]:
        """Return all stored players."""

    def get_dashboard(self, account_id: AccountId) -> PlayerDashboard | None:
        """Return a stored dashboard or None when the player is absent."""


class MatchDetailReader(Protocol):
    """Read a complete match without exposing the external provider."""

    def get_match_detail(self, match_id: int) -> MatchDetail | None:
        """Return match detail or None if the match is absent."""


@runtime_checkable
class OpenDotaGateway(Protocol):
    """Gateway to the OpenDota API (driven/secondary port)."""

    def get_player(self, account_id: AccountId) -> PlayerDTO | None:
        """Fetch a player profile by OpenDota/Steam account id."""

    def get_player_recent_matches(self, account_id: AccountId, limit: int = 20) -> list[MatchDTO]:
        """Fetch recent matches for a player, newest first."""

    def iter_player_matches(
        self, account_id: AccountId, limit: int | None = 20
    ) -> Iterator[MatchDTO]:
        """Stream newest-first matches; None requests all provider-available matches."""

    def get_match(self, match_id: MatchId) -> MatchDTO | None:
        """Fetch a single match by OpenDota match id."""

    def get_heroes(self) -> Sequence[HeroDTO]:
        """Fetch the full hero catalog."""

    def get_items(self) -> Sequence[ItemDTO]:
        """Fetch the full item catalog."""


@runtime_checkable
class UnitOfWork(Protocol):
    """Transaction boundary port used by use cases."""

    def commit(self) -> None:
        """Commit the current unit of work."""

    def rollback(self) -> None:
        """Roll back the current unit of work."""


__all__ = ["DashboardReader", "OpenDotaGateway", "UnitOfWork"]
