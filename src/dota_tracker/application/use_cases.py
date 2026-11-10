"""Application use cases.

Use cases orchestrate domain entities, repositories, and external gateways to
fulfil a single user/business request.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from dota_tracker.application.dtos import (
    HeroDTO,
    ItemDTO,
    MatchDTO,
    PlayerDTO,
    PlayerMatchDTO,
    SyncResult,
)
from dota_tracker.application.ports import OpenDotaGateway, UnitOfWork
from dota_tracker.domain.entities import Hero, Item, Match, Player, PlayerMatch
from dota_tracker.domain.exceptions import PlayerNotFoundError
from dota_tracker.domain.repositories import (
    HeroRepository,
    ItemRepository,
    MatchRepository,
    PlayerMatchRepository,
    PlayerRepository,
)
from dota_tracker.shared.types import AccountId, HeroId, ItemId, MatchId, PlayerId
from dota_tracker.shared.utils import to_datetime


class SyncPlayerMatchesUseCase:
    """Sync a player's profile and recent matches from OpenDota into the store.

    Flow:
    1. Fetch player profile via the OpenDota gateway.
    2. Upsert the player aggregate.
    3. Fetch recent matches; upsert matches plus hero/item catalog entries.
    4. Upsert per-player match participation rows.
    5. Commit the unit of work when one is provided.
    """

    def __init__(
        self,
        gateway: OpenDotaGateway,
        player_repo: PlayerRepository,
        match_repo: MatchRepository,
        player_match_repo: PlayerMatchRepository,
        hero_repo: HeroRepository,
        item_repo: ItemRepository,
        unit_of_work: UnitOfWork | None = None,
    ) -> None:
        self._gateway = gateway
        self._player_repo = player_repo
        self._match_repo = match_repo
        self._player_match_repo = player_match_repo
        self._hero_repo = hero_repo
        self._item_repo = item_repo
        self._unit_of_work = unit_of_work

    def execute(self, account_id: AccountId, limit: int = 20) -> SyncResult:
        """Run the sync for the given account id.

        Args:
            account_id: OpenDota/Steam32 account identifier.
            limit: Maximum number of recent matches to sync.

        Returns:
            A :class:`SyncResult` summarizing what was persisted.

        Raises:
            PlayerNotFoundError: if the OpenDota gateway returns no player.
        """
        result = SyncResult(account_id=int(account_id))

        player_dto = self._gateway.get_player(account_id)
        if player_dto is None:
            raise PlayerNotFoundError(
                f"Player with account_id {account_id} not found in OpenDota",
                details={"account_id": int(account_id)},
            )

        player = self._map_player_dto(player_dto)
        existing_player = self._player_repo.get_by_account_id(player.account_id)
        if existing_player is None:
            player = self._player_repo.add(player)
        else:
            player = self._player_repo.save(
                Player(
                    id=existing_player.id,
                    account_id=player.account_id,
                    persona_name=player.persona_name,
                    steam_id=player.steam_id,
                    avatar_url=player.avatar_url,
                    profile_url=player.profile_url,
                    country_code=player.country_code,
                    last_match_time=player.last_match_time,
                    is_tracked=existing_player.is_tracked,
                )
            )
        result.players_synced = 1

        match_dtos = list(self._gateway.get_player_recent_matches(account_id, limit=limit))

        hero_dtos = list(self._gateway.get_heroes())
        item_dtos = list(self._gateway.get_items())
        self._upsert_catalog(hero_dtos, item_dtos)

        hero_map = {h.hero_id: h for h in self._hero_repo.get_all_active()}

        for match_dto in match_dtos:
            match = self._map_match_dto(match_dto)
            existing = self._match_repo.get_by_external_id(match.match_id)
            if existing is None:
                saved_match = self._match_repo.add(match)
            else:
                saved_match = self._match_repo.save(
                    Match(
                        id=existing.id,
                        match_id=match.match_id,
                        start_time=match.start_time,
                        duration_seconds=match.duration_seconds,
                        game_mode=match.game_mode,
                        lobby_type=match.lobby_type,
                        radiant_win=match.radiant_win,
                        radiant_score=match.radiant_score,
                        dire_score=match.dire_score,
                        patch=match.patch,
                        region=match.region,
                        radiant_team_id=match.radiant_team_id,
                        dire_team_id=match.dire_team_id,
                        outcome=match.compute_outcome(),
                        raw_match=match.raw_match,
                    )
                )
            result.matches_synced += 1

            player_match_dto = self._extract_player_match_dto(match_dto, account_id)
            if player_match_dto is None:
                continue
            hero = hero_map.get(HeroId(player_match_dto.hero_id))
            if hero is None or hero.id is None:
                continue
            player_match = self._map_player_match_dto(
                player_match_dto,
                player_id=player.id,
                account_id=account_id,
                match_internal_id=saved_match.id,
                hero_internal_id=hero.id,
            )
            if player_match.match_id is None:
                continue
            existing_pm = self._player_match_repo.get_by_match_and_slot(
                player_match.match_id, player_match.player_slot
            )
            if existing_pm is None:
                self._player_match_repo.add(player_match)
            else:
                self._player_match_repo.save(
                    PlayerMatch(
                        id=existing_pm.id,
                        match_id=player_match.match_id,
                        player_id=player_match.player_id,
                        account_id=player_match.account_id,
                        hero_id=player_match.hero_id,
                        player_slot=player_match.player_slot,
                        is_radiant=player_match.is_radiant,
                        win=player_match.win,
                        kills=player_match.kills,
                        deaths=player_match.deaths,
                        assists=player_match.assists,
                        gold_per_min=player_match.gold_per_min,
                        xp_per_min=player_match.xp_per_min,
                        last_hits=player_match.last_hits,
                        denies=player_match.denies,
                        hero_damage=player_match.hero_damage,
                        tower_damage=player_match.tower_damage,
                        hero_healing=player_match.hero_healing,
                        level=player_match.level,
                        item_0_id=player_match.item_0_id,
                        item_1_id=player_match.item_1_id,
                        item_2_id=player_match.item_2_id,
                        item_3_id=player_match.item_3_id,
                        item_4_id=player_match.item_4_id,
                        item_5_id=player_match.item_5_id,
                        item_neutral_id=player_match.item_neutral_id,
                        lane=player_match.lane,
                        role=player_match.role,
                    )
                )
            result.player_matches_synced += 1

        if self._unit_of_work is not None:
            self._unit_of_work.commit()

        return result

    # ------------------------------------------------------------------
    # Mapping helpers (DTO -> domain entity)
    # ------------------------------------------------------------------

    @staticmethod
    def _map_player_dto(dto: PlayerDTO) -> Player:
        return Player(
            account_id=AccountId(dto.account_id),
            persona_name=dto.persona_name,
            steam_id=dto.steam_id,
            avatar_url=dto.avatar_url,
            profile_url=dto.profile_url,
            country_code=dto.country_code,
            last_match_time=SyncPlayerMatchesUseCase._to_epoch_datetime(dto.last_match_time),
            is_tracked=dto.is_tracked,
        )

    @staticmethod
    def _map_match_dto(dto: MatchDTO) -> Match:
        return Match(
            match_id=MatchId(dto.match_id),
            start_time=SyncPlayerMatchesUseCase._to_epoch_datetime(dto.start_time),
            duration_seconds=dto.duration_seconds,
            game_mode=dto.game_mode,
            lobby_type=dto.lobby_type,
            radiant_win=dto.radiant_win,
            radiant_score=dto.radiant_score,
            dire_score=dto.dire_score,
            patch=dto.patch,
            region=dto.region,
            radiant_team_id=dto.radiant_team_id,
            dire_team_id=dto.dire_team_id,
        )

    @staticmethod
    def _map_player_match_dto(
        dto: PlayerMatchDTO,
        *,
        player_id: PlayerId | None,
        account_id: AccountId,
        match_internal_id: MatchId | None,
        hero_internal_id: HeroId,
    ) -> PlayerMatch:
        return PlayerMatch(
            match_id=match_internal_id,  # type: ignore[arg-type]
            hero_id=hero_internal_id,
            player_slot=dto.player_slot,
            is_radiant=dto.is_radiant,
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
            item_0_id=None,
            item_1_id=None,
            item_2_id=None,
            item_3_id=None,
            item_4_id=None,
            item_5_id=None,
            item_neutral_id=None,
            lane=dto.lane,
            role=dto.role,
            player_id=player_id,
            account_id=account_id,
        )

    def _upsert_catalog(self, heroes: Sequence[HeroDTO], items: Sequence[ItemDTO]) -> None:
        for dto in heroes:
            hero = Hero(
                hero_id=HeroId(dto.hero_id),
                name=dto.name,
                localized_name=dto.localized_name,
                primary_attr=dto.primary_attr,
                attack_type=dto.attack_type,
                roles=dto.roles,
                legs=dto.legs,
                is_active=dto.is_active,
            )
            existing = self._hero_repo.get_by_external_id(hero.hero_id)
            if existing is None:
                self._hero_repo.add(hero)
            else:
                self._hero_repo.save(
                    Hero(
                        id=existing.id,
                        hero_id=hero.hero_id,
                        name=hero.name,
                        localized_name=hero.localized_name,
                        primary_attr=hero.primary_attr,
                        attack_type=hero.attack_type,
                        roles=hero.roles,
                        legs=hero.legs,
                        is_active=hero.is_active,
                    )
                )
        for item_dto in items:
            item = Item(
                item_id=ItemId(item_dto.item_id),
                name=item_dto.name,
                localized_name=item_dto.localized_name,
                cost=item_dto.cost,
                is_recipe=item_dto.is_recipe,
                in_secret_shop=item_dto.in_secret_shop,
                in_side_shop=item_dto.in_side_shop,
            )
            existing_item = self._item_repo.get_by_external_id(item.item_id)
            if existing_item is None:
                self._item_repo.add(item)
            else:
                self._item_repo.save(
                    Item(
                        id=existing_item.id,
                        item_id=item.item_id,
                        name=item.name,
                        localized_name=item.localized_name,
                        cost=item.cost,
                        is_recipe=item.is_recipe,
                        in_secret_shop=item.in_secret_shop,
                        in_side_shop=item.in_side_shop,
                    )
                )

    @staticmethod
    def _to_epoch_datetime(value: object) -> datetime | None:
        """Convert an OpenDota timestamp (epoch seconds or ISO-8601) to datetime."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return to_datetime(float(value))
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @staticmethod
    def _extract_player_match_dto(dto: MatchDTO, account_id: AccountId) -> PlayerMatchDTO | None:
        """Extract the requesting player's participation from a match DTO.

        OpenDota's ``/players/{account_id}/matches`` endpoint returns each match
        from the requesting player's perspective, including ``player_slot`` and
        per-player stats. Matches without a slot contribute no player row.
        """
        if dto.player_slot is None or dto.hero_id is None:
            return None
        is_radiant = dto.player_slot < 128
        win = dto.win
        if win is None and dto.radiant_win is not None:
            win = dto.radiant_win if is_radiant else (not dto.radiant_win)
        return PlayerMatchDTO(
            match_id=dto.match_id,
            account_id=int(account_id),
            hero_id=dto.hero_id,
            player_slot=dto.player_slot,
            is_radiant=is_radiant,
            win=win,
            kills=dto.kills or 0,
            deaths=dto.deaths or 0,
            assists=dto.assists or 0,
            gold_per_min=dto.gold_per_min,
            xp_per_min=dto.xp_per_min,
            last_hits=dto.last_hits,
            denies=dto.denies,
            hero_damage=dto.hero_damage,
            tower_damage=dto.tower_damage,
            hero_healing=dto.hero_healing,
            level=dto.level,
            item_0_id=dto.item_0_id,
            item_1_id=dto.item_1_id,
            item_2_id=dto.item_2_id,
            item_3_id=dto.item_3_id,
            item_4_id=dto.item_4_id,
            item_5_id=dto.item_5_id,
            item_neutral_id=dto.item_neutral_id,
            lane=dto.lane,
            role=dto.role,
        )


__all__ = ["SyncPlayerMatchesUseCase"]
