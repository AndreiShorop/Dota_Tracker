"""Application DTOs: validated data transferred across layer boundaries.

Pydantic models keep input/output contracts explicit and self-validating,
separate from domain entities and ORM models.

Note: :class:`MatchDTO` carries optional player-centric fields
(``player_slot``, ``kills``, ...). They are populated only when the DTO
originates from OpenDota's ``/players/{account_id}/matches`` endpoint, which
returns each match from the requesting player's perspective.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PlayerDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    account_id: int
    persona_name: str | None = None
    steam_id: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None
    country_code: str | None = None
    last_match_time: str | None = None
    is_tracked: bool = False


class MatchDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    match_id: int
    start_time: str | None = None
    duration_seconds: int | None = Field(default=None, ge=0)
    game_mode: int | None = None
    lobby_type: int | None = None
    radiant_win: bool | None = None
    radiant_score: int | None = None
    dire_score: int | None = None
    patch: int | None = None
    region: int | None = None
    radiant_team_id: int | None = None
    dire_team_id: int | None = None
    # Populated only for player-endpoint responses (per-requesting-player view).
    hero_id: int | None = None
    player_slot: int | None = None
    win: bool | None = None
    kills: int | None = Field(default=None, ge=0)
    deaths: int | None = Field(default=None, ge=0)
    assists: int | None = Field(default=None, ge=0)
    gold_per_min: int | None = Field(default=None, ge=0)
    xp_per_min: int | None = Field(default=None, ge=0)
    last_hits: int | None = Field(default=None, ge=0)
    denies: int | None = Field(default=None, ge=0)
    hero_damage: int | None = Field(default=None, ge=0)
    tower_damage: int | None = Field(default=None, ge=0)
    hero_healing: int | None = Field(default=None, ge=0)
    level: int | None = Field(default=None, ge=0, le=30)
    item_0_id: int | None = None
    item_1_id: int | None = None
    item_2_id: int | None = None
    item_3_id: int | None = None
    item_4_id: int | None = None
    item_5_id: int | None = None
    item_neutral_id: int | None = None
    lane: int | None = None
    role: int | None = None


class HeroDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    hero_id: int
    name: str
    localized_name: str
    primary_attr: str | None = None
    attack_type: str | None = None
    roles: list[str] | None = None
    legs: int | None = None
    is_active: bool = True


class ItemDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    item_id: int
    name: str | None = None
    localized_name: str | None = None
    cost: int | None = Field(default=None, ge=0)
    is_recipe: bool = False
    in_secret_shop: bool = False
    in_side_shop: bool = False


class PlayerMatchDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    match_id: int
    player_id: int | None = None
    account_id: int | None = None
    hero_id: int
    player_slot: int
    is_radiant: bool
    win: bool | None = None
    kills: int = Field(default=0, ge=0)
    deaths: int = Field(default=0, ge=0)
    assists: int = Field(default=0, ge=0)
    gold_per_min: int | None = Field(default=None, ge=0)
    xp_per_min: int | None = Field(default=None, ge=0)
    last_hits: int | None = Field(default=None, ge=0)
    denies: int | None = Field(default=None, ge=0)
    hero_damage: int | None = Field(default=None, ge=0)
    tower_damage: int | None = Field(default=None, ge=0)
    hero_healing: int | None = Field(default=None, ge=0)
    level: int | None = Field(default=None, ge=0, le=30)
    item_0_id: int | None = None
    item_1_id: int | None = None
    item_2_id: int | None = None
    item_3_id: int | None = None
    item_4_id: int | None = None
    item_5_id: int | None = None
    item_neutral_id: int | None = None
    lane: int | None = None
    role: int | None = None


class SyncResult(BaseModel):
    """Outcome of a player sync operation."""

    account_id: int
    players_synced: int = 0
    matches_synced: int = 0
    player_matches_synced: int = 0


__all__ = [
    "HeroDTO",
    "ItemDTO",
    "MatchDTO",
    "PlayerDTO",
    "PlayerMatchDTO",
    "SyncResult",
]
