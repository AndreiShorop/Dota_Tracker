"""Domain entities: core business objects with identity and lifecycle.

Entities are immutable frozen dataclasses. Infrastructure and application
layers map between these entities and ORM/API models at the boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from dota_tracker.domain.value_objects import MatchOutcome
from dota_tracker.shared.types import (
    AccountId,
    DurationSeconds,
    HeroId,
    ItemId,
    MatchId,
    PlayerId,
)


@dataclass(frozen=True)
class Player:
    """A tracked Dota 2 player/account."""

    account_id: AccountId
    persona_name: str | None = None
    steam_id: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None
    country_code: str | None = None
    last_match_time: datetime | None = None
    is_tracked: bool = False
    raw_profile: dict[str, Any] | None = None
    id: PlayerId | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Match:
    """A single Dota 2 match."""

    match_id: MatchId
    start_time: datetime | None = None
    duration_seconds: DurationSeconds | None = None
    game_mode: int | None = None
    lobby_type: int | None = None
    radiant_win: bool | None = None
    radiant_score: int | None = None
    dire_score: int | None = None
    patch: int | None = None
    region: int | None = None
    radiant_team_id: int | None = None
    dire_team_id: int | None = None
    outcome: MatchOutcome = MatchOutcome.UNKNOWN
    raw_match: dict[str, Any] | None = None
    id: MatchId | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def compute_outcome(self) -> MatchOutcome:
        """Derive the match outcome from stored fields."""
        if self.radiant_win is True:
            return MatchOutcome.RADIANT_WIN
        if self.radiant_win is False:
            return MatchOutcome.DIRE_WIN
        return MatchOutcome.UNKNOWN


@dataclass(frozen=True)
class Hero:
    """Canonical Dota 2 hero catalog entry."""

    hero_id: HeroId
    name: str
    localized_name: str
    primary_attr: str | None = None
    attack_type: str | None = None
    roles: list[str] | None = None
    legs: int | None = None
    is_active: bool = True
    raw_data: dict[str, Any] | None = None
    id: HeroId | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Item:
    """Canonical Dota 2 item catalog entry."""

    item_id: ItemId
    name: str | None = None
    localized_name: str | None = None
    cost: int | None = None
    is_recipe: bool = False
    in_secret_shop: bool = False
    in_side_shop: bool = False
    raw_data: dict[str, Any] | None = None
    id: ItemId | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class PlayerMatch:
    """Per-player participation and performance within a match (fact row)."""

    match_id: MatchId
    hero_id: HeroId
    player_slot: int
    is_radiant: bool
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    gold_per_min: int | None = None
    xp_per_min: int | None = None
    last_hits: int | None = None
    denies: int | None = None
    hero_damage: int | None = None
    tower_damage: int | None = None
    hero_healing: int | None = None
    level: int | None = None
    item_0_id: ItemId | None = None
    item_1_id: ItemId | None = None
    item_2_id: ItemId | None = None
    item_3_id: ItemId | None = None
    item_4_id: ItemId | None = None
    item_5_id: ItemId | None = None
    item_neutral_id: ItemId | None = None
    lane: int | None = None
    role: int | None = None
    win: bool | None = None
    player_id: PlayerId | None = None
    account_id: AccountId | None = None
    raw_player: dict[str, Any] | None = None
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @property
    def kda(self) -> tuple[int, int, int]:
        """Kill/death/assist counts."""
        return self.kills, self.deaths, self.assists
