"""Mappers between OpenDota response models and application DTOs."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError

from dota_tracker.application.dtos import (
    HeroDTO,
    ItemDTO,
    MatchDTO,
    PlayerDTO,
)
from dota_tracker.infrastructure.opendota.exceptions import (
    OpenDotaResponseValidationError,
)
from dota_tracker.infrastructure.opendota.models import (
    OpenDotaHero,
    OpenDotaItem,
    OpenDotaMatch,
    OpenDotaPlayer,
)
from dota_tracker.shared.utils import to_datetime

TModel = TypeVar("TModel", bound=BaseModel)


def map_player(dto: OpenDotaPlayer) -> PlayerDTO:
    """Map an OpenDota player response to a PlayerDTO.

    OpenDota nests profile fields under ``profile`` (personaname, steamid,
    avatar/avatarfull, profileurl, loccountrycode, last_match_time) while
    ``account_id`` is top-level or may appear inside ``profile``.
    """
    profile = dto.profile
    account_id = dto.account_id
    if account_id is None and profile is not None:
        account_id = profile.account_id
    if account_id is None:
        raise OpenDotaResponseValidationError("OpenDota player response missing account_id")
    return PlayerDTO(
        account_id=account_id,
        persona_name=profile.personaname if profile else None,
        steam_id=profile.steamid if profile else None,
        avatar_url=(profile.avatar or profile.avatarfull) if profile else None,
        profile_url=profile.profileurl if profile else None,
        country_code=profile.loccountrycode if profile else None,
        is_tracked=False,
    )


def map_match(dto: OpenDotaMatch) -> MatchDTO:
    """Map an OpenDota match response to a MatchDTO."""

    def epoch(value: int | None) -> str | None:
        if value is None:
            return None
        dt = to_datetime(float(value))
        return dt.isoformat() if dt is not None else None

    return MatchDTO(
        match_id=dto.match_id,
        start_time=epoch(dto.start_time),
        duration_seconds=dto.duration,
        game_mode=dto.game_mode,
        lobby_type=dto.lobby_type,
        radiant_win=dto.radiant_win,
        radiant_score=dto.radiant_score,
        dire_score=dto.dire_score,
        patch=dto.patch,
        region=dto.region,
        radiant_team_id=dto.radiant_team_id,
        dire_team_id=dto.dire_team_id,
        hero_id=dto.hero_id,
        player_slot=dto.player_slot,
        win=dto.win,
        kills=dto.kills,
        deaths=dto.deaths,
        assists=dto.assists,
        gold_per_min=dto.gold_per_min,
        xp_per_min=dto.xp_per_min,
        last_hits=dto.last_hits,
        denies=dto.denies,
        hero_damage=dto.hero_damage,
        tower_damage=dto.tower_damage,
        hero_healing=dto.hero_healing,
        level=dto.level,
        item_0_id=dto.item_0,
        item_1_id=dto.item_1,
        item_2_id=dto.item_2,
        item_3_id=dto.item_3,
        item_4_id=dto.item_4,
        item_5_id=dto.item_5,
        item_neutral_id=dto.neutral_item,
        lane=dto.lane,
        role=dto.role,
    )


def map_hero(dto: OpenDotaHero) -> HeroDTO:
    return HeroDTO(
        hero_id=dto.id,
        name=dto.name,
        localized_name=dto.localized_name,
        primary_attr=dto.primary_attr,
        attack_type=dto.attack_type,
        roles=dto.roles,
        legs=dto.legs,
        is_active=True,
    )


def map_item(dto: OpenDotaItem) -> ItemDTO:
    return ItemDTO(
        item_id=dto.id,
        name=dto.name,
        localized_name=dto.localized_name,
        cost=dto.cost,
        is_recipe=dto.is_recipe,
        in_side_shop=dto.side_shop if dto.side_shop is not None else False,
    )


def parse_model(model_type: type[TModel], payload: object) -> TModel:  # noqa: UP047
    """Parse raw JSON into a pydantic model, translating validation errors."""
    try:
        return model_type.model_validate(payload)
    except PydanticValidationError as exc:
        raise OpenDotaResponseValidationError(
            f"OpenDota response validation failed: {exc}"
        ) from exc


__all__ = ["map_hero", "map_item", "map_match", "map_player", "parse_model"]
