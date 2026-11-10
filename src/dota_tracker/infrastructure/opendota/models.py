"""Pydantic response models for OpenDota API payloads.

Extra fields are tolerated (provider drift) while normalized fields remain
strict. These models describe the transport format only and never leak across
the port boundary.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OpenDotaPlayerProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    account_id: int | None = None
    personaname: str | None = None
    name: str | None = None
    steamid: str | None = None
    avatar: str | None = None
    avatarfull: str | None = None
    profileurl: str | None = None
    loccountrycode: str | None = None
    last_match_time: int | None = Field(default=None, description="Unix epoch seconds")


class OpenDotaPlayer(BaseModel):
    model_config = ConfigDict(extra="allow")

    account_id: int | None = None
    profile: OpenDotaPlayerProfile | None = None
    mmr_estimate: dict[str, Any] | None = None
    rank_tier: int | None = None

    @model_validator(mode="before")
    @classmethod
    def _lift_account_id(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("account_id") is None:
            profile = data.get("profile")
            if isinstance(profile, dict) and profile.get("account_id") is not None:
                data = {**data, "account_id": profile["account_id"]}
        return data


class OpenDotaMatch(BaseModel):
    model_config = ConfigDict(extra="allow")

    match_id: int
    start_time: int | None = Field(default=None, description="Unix epoch seconds")
    duration: int | None = Field(default=None, ge=0)
    game_mode: int | None = None
    lobby_type: int | None = None
    radiant_win: bool | None = None
    radiant_score: int | None = None
    dire_score: int | None = None
    patch: int | None = None
    region: int | None = None
    radiant_team_id: int | None = None
    dire_team_id: int | None = None
    # Populated by /players/{account_id}/matches (requesting player's view).
    player_slot: int | None = None
    hero_id: int | None = None
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
    item_0: int | None = Field(default=None, description="OpenDota item slot field name")
    item_1: int | None = None
    item_2: int | None = None
    item_3: int | None = None
    item_4: int | None = None
    item_5: int | None = None
    neutral_item: int | None = None
    lane: int | None = None
    role: int | None = None


class OpenDotaHero(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    name: str
    localized_name: str
    primary_attr: str | None = None
    attack_type: str | None = None
    roles: list[str] | None = None
    legs: int | None = None


class OpenDotaItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    name: str | None = None
    localized_name: str | None = None
    cost: int | None = Field(default=None, ge=0)
    is_recipe: bool = False
    side_shop: bool | None = Field(default=None, alias="in_side_shop")


__all__ = ["OpenDotaHero", "OpenDotaItem", "OpenDotaMatch", "OpenDotaPlayer"]
