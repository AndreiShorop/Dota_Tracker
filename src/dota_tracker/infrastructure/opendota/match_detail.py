"""OpenDota match-detail adapter and reusable catalog metadata cache."""

from __future__ import annotations

import re
import time
from datetime import UTC, datetime
from threading import Lock

from pydantic import BaseModel, ConfigDict, Field, RootModel

from dota_tracker.application.dtos import MatchDetail, MatchDetailItem, MatchDetailPlayer
from dota_tracker.infrastructure.opendota.client import OpenDotaClient
from dota_tracker.infrastructure.opendota.exceptions import (
    OpenDotaNotFoundError,
    OpenDotaResponseValidationError,
)
from dota_tracker.infrastructure.opendota.mappers import parse_model


class OpenDotaMatchPlayer(BaseModel):
    """The fields actually used from a match participant."""

    model_config = ConfigDict(extra="ignore")

    account_id: int | None = Field(default=None, ge=0, le=4294967295)
    player_slot: int | None = Field(default=None, ge=0, le=255)
    hero_id: int | None = Field(default=None, ge=0)
    personaname: str | None = None
    name: str | None = None
    kills: int | None = Field(default=None, ge=0)
    deaths: int | None = Field(default=None, ge=0)
    assists: int | None = Field(default=None, ge=0)
    gold_per_min: int | None = Field(default=None, ge=0)
    xp_per_min: int | None = Field(default=None, ge=0)
    last_hits: int | None = Field(default=None, ge=0)
    hero_damage: int | None = Field(default=None, ge=0)
    tower_damage: int | None = Field(default=None, ge=0)
    hero_healing: int | None = Field(default=None, ge=0)
    level: int | None = Field(default=None, ge=0)
    item_0: int | None = Field(default=None, ge=0)
    item_1: int | None = Field(default=None, ge=0)
    item_2: int | None = Field(default=None, ge=0)
    item_3: int | None = Field(default=None, ge=0)
    item_4: int | None = Field(default=None, ge=0)
    item_5: int | None = Field(default=None, ge=0)
    backpack_0: int | None = Field(default=None, ge=0)
    backpack_1: int | None = Field(default=None, ge=0)
    backpack_2: int | None = Field(default=None, ge=0)
    backpack_3: int | None = Field(default=None, ge=0)
    item_neutral: int | None = Field(default=None, ge=0)
    item_neutral2: int | None = Field(default=None, ge=0)


class OpenDotaMatchDetail(BaseModel):
    """Transport model for the match and its participant list."""

    model_config = ConfigDict(extra="ignore")

    match_id: int = Field(gt=0)
    start_time: int | None = Field(default=None, ge=0, le=253402300799)
    duration: int | None = Field(default=None, ge=0)
    radiant_win: bool | None = None
    radiant_score: int | None = Field(default=None, ge=0)
    dire_score: int | None = Field(default=None, ge=0)
    players: list[OpenDotaMatchPlayer]


class CatalogHero(BaseModel):
    """Relevant fields from the hero constants."""

    id: int = Field(gt=0)
    localized_name: str | None = None
    img: str | None = None


class CatalogItem(BaseModel):
    """Relevant fields from the item constants, including unnumbered entries."""

    id: int | None = Field(default=None, ge=0)
    dname: str | None = None
    img: str | None = None


class HeroCatalog(RootModel[dict[str, CatalogHero]]):
    """OpenDota heroes keyed by registry ID."""


class ItemCatalog(RootModel[dict[str, CatalogItem]]):
    """OpenDota items keyed by registry name."""


def _json(client: OpenDotaClient, path: str) -> object:
    response = client.get(path)
    try:
        return response.json()
    except ValueError as exc:
        raise OpenDotaResponseValidationError("OpenDota returned invalid JSON") from exc


def _image(path: str | None, category: str) -> str | None:
    """Accept only known relative Steam asset paths; never trust a remote URL."""
    if path is None:
        return None
    asset = path.partition("?")[0]
    pattern = rf"/apps/dota2/images/dota_react/{category}/[a-z0-9_]+\.png"
    if re.fullmatch(pattern, asset) is None:
        return None
    return f"https://cdn.cloudflare.steamstatic.com{asset}"


class MatchCatalogCache:
    """Cache validated catalogs per provider URL for one hour, across requests."""

    def __init__(self, ttl_seconds: float = 3600) -> None:
        self._ttl_seconds = ttl_seconds
        self._lock = Lock()
        self._entries: dict[str, tuple[float, dict[int, CatalogHero], dict[int, CatalogItem]]] = {}

    def get(
        self, client: OpenDotaClient, provider: str
    ) -> tuple[dict[int, CatalogHero], dict[int, CatalogItem]]:
        """Get cached catalogs, loading both atomically if missing or expired."""
        with self._lock:
            cached = self._entries.get(provider)
            if cached is not None and time.monotonic() < cached[0]:
                return cached[1], cached[2]
            heroes = parse_model(HeroCatalog, _json(client, "/constants/heroes"))
            items = parse_model(ItemCatalog, _json(client, "/constants/items"))
            hero_map = {hero.id: hero for hero in heroes.root.values()}
            item_map = {item.id: item for item in items.root.values() if item.id is not None}
            self._entries[provider] = (time.monotonic() + self._ttl_seconds, hero_map, item_map)
            return hero_map, item_map


class OpenDotaMatchDetailReader:
    """Fetch one match and enrich it with validated, cached provider metadata."""

    def __init__(self, client: OpenDotaClient, cache: MatchCatalogCache, provider: str) -> None:
        self._client = client
        self._cache = cache
        self._provider = provider

    def get_match_detail(self, match_id: int) -> MatchDetail | None:
        """Read the requested match, or return None for an absent match."""
        try:
            payload = _json(self._client, f"/matches/{match_id}")
        except OpenDotaNotFoundError:
            return None
        if payload is None:
            return None
        match = parse_model(OpenDotaMatchDetail, payload)
        if match.match_id != match_id:
            raise OpenDotaResponseValidationError("OpenDota returned a different match ID")
        heroes, items = self._cache.get(self._client, self._provider)
        try:
            start_time = (
                datetime.fromtimestamp(match.start_time, tz=UTC)
                if match.start_time is not None
                else None
            )
        except (OverflowError, OSError, ValueError) as exc:
            raise OpenDotaResponseValidationError("Invalid match start time") from exc
        return MatchDetail(
            match_id=match.match_id,
            start_time=start_time,
            duration_seconds=match.duration,
            radiant_win=match.radiant_win,
            radiant_score=match.radiant_score,
            dire_score=match.dire_score,
            players=[
                self._player(player, match.radiant_win, heroes, items) for player in match.players
            ],
        )

    @staticmethod
    def _player(
        player: OpenDotaMatchPlayer,
        radiant_win: bool | None,
        heroes: dict[int, CatalogHero],
        items: dict[int, CatalogItem],
    ) -> MatchDetailPlayer:
        hero = heroes.get(player.hero_id) if player.hero_id is not None else None
        inventory = (
            player.item_0, player.item_1, player.item_2, player.item_3, player.item_4,
            player.item_5, player.backpack_0, player.backpack_1, player.backpack_2,
            player.backpack_3, player.item_neutral, player.item_neutral2,
        )
        final_items = []
        for slot, item_id in enumerate(inventory):
            if item_id is None or item_id == 0:
                continue
            item = items.get(item_id)
            final_items.append(MatchDetailItem(
                slot=slot, id=item_id, name=item.dname if item else None,
                image=_image(item.img, "items") if item else None,
            ))
        win = None
        if player.player_slot is not None and radiant_win is not None:
            win = radiant_win == (player.player_slot < 128)
        return MatchDetailPlayer(
            account_id=player.account_id if player.account_id != 4294967295 else None,
            player_slot=player.player_slot,
            hero_id=player.hero_id,
            hero_name=hero.localized_name if hero else None,
            hero_image=_image(hero.img, "heroes") if hero else None,
            persona_name=player.personaname or player.name,
            win=win,
            kills=player.kills,
            deaths=player.deaths,
            assists=player.assists,
            gold_per_min=player.gold_per_min,
            xp_per_min=player.xp_per_min,
            last_hits=player.last_hits,
            hero_damage=player.hero_damage,
            tower_damage=player.tower_damage,
            hero_healing=player.hero_healing,
            level=player.level,
            items=final_items,
        )
