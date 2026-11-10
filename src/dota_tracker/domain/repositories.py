"""Repository ports for the domain layer.

These abstract base classes define the persistence contract that application
use cases depend on. Concrete implementations live in the infrastructure
layer (e.g. SQLAlchemy-backed repositories).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Generic, TypeVar

from dota_tracker.domain.entities import Hero, Item, Match, Player, PlayerMatch
from dota_tracker.shared.types import AccountId, HeroId, ItemId, MatchId, PlayerId

TEntity = TypeVar("TEntity")


class Repository(Generic[TEntity], ABC):  # noqa: UP046
    """Base repository interface."""

    @abstractmethod
    def add(self, entity: TEntity) -> TEntity:
        """Persist a new entity and return it with any assigned identity."""

    @abstractmethod
    def save(self, entity: TEntity) -> TEntity:
        """Persist updates to an existing entity and return it."""


class PlayerRepository(Repository[Player]):
    """Persistence port for :class:`Player` aggregates."""

    @abstractmethod
    def get_by_id(self, player_id: PlayerId) -> Player | None:
        """Return the player with the given internal id, or None."""

    @abstractmethod
    def get_by_account_id(self, account_id: AccountId) -> Player | None:
        """Return the tracked player with the given OpenDota/Steam account id."""

    @abstractmethod
    def list_tracked(self) -> Sequence[Player]:
        """Return all players flagged for active tracking."""

    @abstractmethod
    def add(self, player: Player) -> Player:
        """Insert a new player."""

    @abstractmethod
    def save(self, player: Player) -> Player:
        """Update an existing player."""


class MatchRepository(Repository[Match]):
    """Persistence port for :class:`Match` aggregates."""

    @abstractmethod
    def get_by_id(self, match_id: MatchId) -> Match | None:
        """Return the match with the given internal id, or None."""

    @abstractmethod
    def get_by_external_id(self, match_id: MatchId) -> Match | None:
        """Return the match with the given OpenDota match id, or None."""

    @abstractmethod
    def add(self, match: Match) -> Match:
        """Insert a new match."""

    @abstractmethod
    def save(self, match: Match) -> Match:
        """Update an existing match."""


class HeroRepository(Repository[Hero]):
    """Persistence port for the hero catalog."""

    @abstractmethod
    def get_by_id(self, hero_id: HeroId) -> Hero | None:
        """Return the hero with the given internal id, or None."""

    @abstractmethod
    def get_by_external_id(self, hero_id: HeroId) -> Hero | None:
        """Return the hero with the given OpenDota hero id, or None."""

    @abstractmethod
    def get_all_active(self) -> Sequence[Hero]:
        """Return all active heroes."""

    @abstractmethod
    def add(self, hero: Hero) -> Hero:
        """Insert a new hero."""

    @abstractmethod
    def save(self, hero: Hero) -> Hero:
        """Update an existing hero."""


class ItemRepository(Repository[Item]):
    """Persistence port for the item catalog."""

    @abstractmethod
    def get_by_id(self, item_id: ItemId) -> Item | None:
        """Return the item with the given internal id, or None."""

    @abstractmethod
    def get_by_external_id(self, item_id: ItemId) -> Item | None:
        """Return the item with the given OpenDota item id, or None."""

    @abstractmethod
    def get_all(self) -> Sequence[Item]:
        """Return all catalog items."""

    @abstractmethod
    def add(self, item: Item) -> Item:
        """Insert a new item."""

    @abstractmethod
    def save(self, item: Item) -> Item:
        """Update an existing item."""


class PlayerMatchRepository(Repository[PlayerMatch]):
    """Persistence port for :class:`PlayerMatch` fact rows."""

    @abstractmethod
    def get_by_id(self, row_id: int) -> PlayerMatch | None:
        """Return the player-match row with the given internal id."""

    @abstractmethod
    def get_by_match_and_slot(self, match_id: MatchId, player_slot: int) -> PlayerMatch | None:
        """Return the row for a match slot, or None."""

    @abstractmethod
    def list_by_match(self, match_id: MatchId) -> Sequence[PlayerMatch]:
        """Return all player-match rows for a match."""

    @abstractmethod
    def list_by_player(self, player_id: PlayerId) -> Sequence[PlayerMatch]:
        """Return all player-match rows for a tracked player."""

    @abstractmethod
    def add(self, player_match: PlayerMatch) -> PlayerMatch:
        """Insert a new player-match row."""

    @abstractmethod
    def save(self, player_match: PlayerMatch) -> PlayerMatch:
        """Update an existing player-match row."""
