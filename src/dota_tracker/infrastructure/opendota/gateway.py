"""OpenDota gateway adapter implementing the application :class:`OpenDotaGateway` port.

Translates application requests into OpenDota endpoints and maps responses to
application DTOs. All HTTP concerns are delegated to :class:`OpenDotaClient`.
"""

from __future__ import annotations

from collections.abc import Sequence

from dota_tracker.application.dtos import (
    HeroDTO,
    ItemDTO,
    MatchDTO,
    PlayerDTO,
)
from dota_tracker.infrastructure.opendota.client import OpenDotaClient
from dota_tracker.infrastructure.opendota.exceptions import OpenDotaNotFoundError
from dota_tracker.infrastructure.opendota.mappers import (
    map_hero,
    map_item,
    map_match,
    map_player,
    parse_model,
)
from dota_tracker.infrastructure.opendota.models import (
    OpenDotaHero,
    OpenDotaItem,
    OpenDotaMatch,
    OpenDotaPlayer,
)
from dota_tracker.shared.types import AccountId


class OpenDotaGateway:
    """Infrastructure adapter for the OpenDotaGateway port."""

    def __init__(self, client: OpenDotaClient) -> None:
        self._client = client

    def get_player(self, account_id: AccountId) -> PlayerDTO | None:
        try:
            response = self._client.get(f"/players/{int(account_id)}")
        except OpenDotaNotFoundError:
            return None
        dto = parse_model(OpenDotaPlayer, response.json())
        return map_player(dto)

    def get_player_recent_matches(self, account_id: AccountId, limit: int = 20) -> list[MatchDTO]:
        response = self._client.get(
            f"/players/{int(account_id)}/matches",
            params={"limit": min(max(limit, 1), 100)},
        )
        payload = response.json()
        if not isinstance(payload, list):
            return []
        return [
            map_match(parse_model(OpenDotaMatch, item))
            for item in payload
            if isinstance(item, dict)
        ]

    def get_match(self, match_id: int) -> MatchDTO | None:
        try:
            response = self._client.get(f"/matches/{int(match_id)}")
        except OpenDotaNotFoundError:
            return None
        dto = parse_model(OpenDotaMatch, response.json())
        return map_match(dto)

    def get_heroes(self) -> Sequence[HeroDTO]:
        try:
            response = self._client.get("/heroes")
        except OpenDotaNotFoundError:
            return []
        payload = response.json()
        if not isinstance(payload, list):
            return []
        return [
            map_hero(parse_model(OpenDotaHero, item)) for item in payload if isinstance(item, dict)
        ]

    def get_items(self) -> Sequence[ItemDTO]:
        try:
            response = self._client.get("/items")
        except OpenDotaNotFoundError:
            return []
        payload = response.json()
        if not isinstance(payload, list):
            return []
        return [
            map_item(parse_model(OpenDotaItem, item)) for item in payload if isinstance(item, dict)
        ]


__all__ = ["OpenDotaGateway"]
