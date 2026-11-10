"""OpenDota gateway adapter implementing the application :class:`OpenDotaGateway` port.

Translates application requests into OpenDota endpoints and maps responses to
application DTOs. All HTTP concerns are delegated to :class:`OpenDotaClient`.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence

from dota_tracker.application.dtos import (
    HeroDTO,
    ItemDTO,
    MatchDTO,
    PlayerDTO,
)
from dota_tracker.infrastructure.opendota.client import OpenDotaClient
from dota_tracker.infrastructure.opendota.exceptions import (
    OpenDotaNotFoundError,
    OpenDotaResponseValidationError,
)
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

MATCH_PAGE_SIZE = 100


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
        """Return up to limit matches, retained for existing callers."""
        return list(self.iter_player_matches(account_id, limit))

    def iter_player_matches(
        self, account_id: AccountId, limit: int | None = 20
    ) -> Iterator[MatchDTO]:
        """Read bounded pages using OpenDota's offset and descending match ID order."""
        if not 1 <= int(account_id) <= 4294967295:
            raise ValueError("Invalid account ID")
        if limit is not None and (isinstance(limit, bool) or limit < 1):
            raise ValueError("Match limit must be positive or None")

        offset = 0
        seen: set[int] = set()
        lowest_id: int | None = None
        while limit is None or len(seen) < limit:
            page_size = (
                MATCH_PAGE_SIZE if limit is None else min(MATCH_PAGE_SIZE, limit - len(seen))
            )
            response = self._client.get(
                f"/players/{int(account_id)}/matches",
                params={"limit": page_size, "offset": offset, "significant": 0},
            )
            try:
                payload = response.json()
            except ValueError as exc:
                raise OpenDotaResponseValidationError("Invalid match history JSON") from exc
            if not isinstance(payload, list) or len(payload) > page_size:
                raise OpenDotaResponseValidationError("Invalid match history page")
            if not payload:
                return
            offset += len(payload)
            page_progress = False
            for item in payload:
                if not isinstance(item, dict):
                    raise OpenDotaResponseValidationError("Invalid match history entry")
                match = map_match(parse_model(OpenDotaMatch, item))
                if not 1 <= match.match_id <= 9223372036854775807:
                    raise OpenDotaResponseValidationError("Invalid match ID in history")
                if match.match_id in seen:
                    continue
                if lowest_id is not None and match.match_id > lowest_id:
                    raise OpenDotaResponseValidationError("Match history order changed during sync")
                seen.add(match.match_id)
                lowest_id = match.match_id
                page_progress = True
                yield match
            if not page_progress:
                raise OpenDotaResponseValidationError("Match history pagination made no progress")

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
