"""SQLAlchemy implementations of the domain repository ports."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from dota_tracker.domain.entities import Hero, Item, Match, Player, PlayerMatch
from dota_tracker.domain.repositories import (
    HeroRepository,
    ItemRepository,
    MatchRepository,
    PlayerMatchRepository,
    PlayerRepository,
)
from dota_tracker.infrastructure.models import (
    Hero as HeroModel,
)
from dota_tracker.infrastructure.models import (
    Item as ItemModel,
)
from dota_tracker.infrastructure.models import (
    Match as MatchModel,
)
from dota_tracker.infrastructure.models import (
    Player as PlayerModel,
)
from dota_tracker.infrastructure.models import (
    PlayerMatch as PlayerMatchModel,
)
from dota_tracker.shared.types import AccountId, HeroId, ItemId, MatchId, PlayerId

# ---------------------------------------------------------------------------
# mappers: domain entity <-> ORM model
# ---------------------------------------------------------------------------


def _player_to_domain(model: PlayerModel) -> Player:
    return Player(
        id=PlayerId(model.id) if model.id is not None else None,
        account_id=AccountId(model.account_id),
        steam_id=model.steam_id,
        persona_name=model.persona_name,
        avatar_url=model.avatar_url,
        profile_url=model.profile_url,
        country_code=model.country_code,
        last_match_time=model.last_match_time,
        is_tracked=model.is_tracked,
        raw_profile=model.raw_profile,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _player_to_orm(player: Player) -> PlayerModel:
    return PlayerModel(
        id=player.id,
        account_id=player.account_id,
        steam_id=player.steam_id,
        persona_name=player.persona_name,
        avatar_url=player.avatar_url,
        profile_url=player.profile_url,
        country_code=player.country_code,
        last_match_time=player.last_match_time,
        is_tracked=player.is_tracked,
        raw_profile=player.raw_profile,
    )


def _match_to_domain(model: MatchModel) -> Match:
    return Match(
        id=MatchId(model.id) if model.id is not None else None,
        match_id=MatchId(model.match_id),
        start_time=model.start_time,
        duration_seconds=model.duration_seconds,
        game_mode=model.game_mode,
        lobby_type=model.lobby_type,
        radiant_win=model.radiant_win,
        radiant_score=model.radiant_score,
        dire_score=model.dire_score,
        patch=model.patch,
        region=model.region,
        radiant_team_id=model.radiant_team_id,
        dire_team_id=model.dire_team_id,
        raw_match=model.raw_match,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _match_to_orm(match: Match) -> MatchModel:
    return MatchModel(
        id=match.id,
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
        raw_match=match.raw_match,
    )


def _hero_to_domain(model: HeroModel) -> Hero:
    return Hero(
        id=HeroId(model.id) if model.id is not None else None,
        hero_id=HeroId(model.hero_id),
        name=model.name,
        localized_name=model.localized_name,
        primary_attr=model.primary_attr,
        attack_type=model.attack_type,
        roles=list(model.roles or []),
        legs=model.legs,
        is_active=model.is_active,
        raw_data=model.raw_data,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _hero_to_orm(hero: Hero) -> HeroModel:
    return HeroModel(
        id=hero.id,
        hero_id=hero.hero_id,
        name=hero.name,
        localized_name=hero.localized_name,
        primary_attr=hero.primary_attr,
        attack_type=hero.attack_type,
        roles=hero.roles,
        legs=hero.legs,
        is_active=hero.is_active,
        raw_data=hero.raw_data,
    )


def _item_to_domain(model: ItemModel) -> Item:
    return Item(
        id=ItemId(model.id) if model.id is not None else None,
        item_id=ItemId(model.item_id),
        name=model.name,
        localized_name=model.localized_name,
        cost=model.cost,
        is_recipe=model.is_recipe,
        in_secret_shop=model.in_secret_shop,
        in_side_shop=model.in_side_shop,
        raw_data=model.raw_data,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _item_to_orm(item: Item) -> ItemModel:
    return ItemModel(
        id=item.id,
        item_id=item.item_id,
        name=item.name,
        localized_name=item.localized_name,
        cost=item.cost,
        is_recipe=item.is_recipe,
        in_secret_shop=item.in_secret_shop,
        in_side_shop=item.in_side_shop,
        raw_data=item.raw_data,
    )


def _player_match_to_domain(model: PlayerMatchModel) -> PlayerMatch:
    return PlayerMatch(
        id=model.id,
        match_id=MatchId(model.match_id),
        player_id=PlayerId(model.player_id) if model.player_id is not None else None,
        account_id=AccountId(model.account_id) if model.account_id is not None else None,
        hero_id=HeroId(model.hero_id),
        player_slot=model.player_slot,
        is_radiant=model.is_radiant,
        win=model.win,
        kills=model.kills,
        deaths=model.deaths,
        assists=model.assists,
        gold_per_min=model.gold_per_min,
        xp_per_min=model.xp_per_min,
        last_hits=model.last_hits,
        denies=model.denies,
        hero_damage=model.hero_damage,
        tower_damage=model.tower_damage,
        hero_healing=model.hero_healing,
        level=model.level,
        item_0_id=ItemId(model.item_0_id) if model.item_0_id is not None else None,
        item_1_id=ItemId(model.item_1_id) if model.item_1_id is not None else None,
        item_2_id=ItemId(model.item_2_id) if model.item_2_id is not None else None,
        item_3_id=ItemId(model.item_3_id) if model.item_3_id is not None else None,
        item_4_id=ItemId(model.item_4_id) if model.item_4_id is not None else None,
        item_5_id=ItemId(model.item_5_id) if model.item_5_id is not None else None,
        item_neutral_id=(
            ItemId(model.item_neutral_id) if model.item_neutral_id is not None else None
        ),
        lane=model.lane,
        role=model.role,
        raw_player=model.raw_player,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _player_match_to_orm(pm: PlayerMatch) -> PlayerMatchModel:
    return PlayerMatchModel(
        id=pm.id,
        match_id=pm.match_id,
        player_id=pm.player_id,
        account_id=pm.account_id,
        hero_id=pm.hero_id,
        player_slot=pm.player_slot,
        is_radiant=pm.is_radiant,
        win=pm.win,
        kills=pm.kills,
        deaths=pm.deaths,
        assists=pm.assists,
        gold_per_min=pm.gold_per_min,
        xp_per_min=pm.xp_per_min,
        last_hits=pm.last_hits,
        denies=pm.denies,
        hero_damage=pm.hero_damage,
        tower_damage=pm.tower_damage,
        hero_healing=pm.hero_healing,
        level=pm.level,
        item_0_id=pm.item_0_id,
        item_1_id=pm.item_1_id,
        item_2_id=pm.item_2_id,
        item_3_id=pm.item_3_id,
        item_4_id=pm.item_4_id,
        item_5_id=pm.item_5_id,
        item_neutral_id=pm.item_neutral_id,
        lane=pm.lane,
        role=pm.role,
        raw_player=pm.raw_player,
    )


class SqlAlchemyPlayerRepository(PlayerRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, player_id: PlayerId) -> Player | None:
        model = self._session.get(PlayerModel, player_id)
        return _player_to_domain(model) if model is not None else None

    def get_by_account_id(self, account_id: AccountId) -> Player | None:
        model = self._session.execute(
            select(PlayerModel).where(PlayerModel.account_id == account_id)
        ).scalar_one_or_none()
        return _player_to_domain(model) if model is not None else None

    def list_tracked(self) -> Sequence[Player]:
        models = (
            self._session.execute(
                select(PlayerModel).where(PlayerModel.is_tracked == True)  # noqa: E712
            )
            .scalars()
            .all()
        )
        return [_player_to_domain(m) for m in models]

    def add(self, player: Player) -> Player:
        model = _player_to_orm(player)
        self._session.add(model)
        self._session.flush()
        return _player_to_domain(model)

    def save(self, player: Player) -> Player:
        model = self._session.get(PlayerModel, player.id) if player.id is not None else None
        if model is None:
            raise ValueError(f"Player with id {player.id} not found")
        for field, value in {
            "account_id": player.account_id,
            "steam_id": player.steam_id,
            "persona_name": player.persona_name,
            "avatar_url": player.avatar_url,
            "profile_url": player.profile_url,
            "country_code": player.country_code,
            "last_match_time": player.last_match_time,
            "is_tracked": player.is_tracked,
            "raw_profile": player.raw_profile,
        }.items():
            setattr(model, field, value)
        self._session.flush()
        return _player_to_domain(model)


class SqlAlchemyMatchRepository(MatchRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, match_id: MatchId) -> Match | None:
        model = self._session.get(MatchModel, match_id)
        return _match_to_domain(model) if model is not None else None

    def get_by_external_id(self, match_id: MatchId) -> Match | None:
        model = self._session.execute(
            select(MatchModel).where(MatchModel.match_id == match_id)
        ).scalar_one_or_none()
        return _match_to_domain(model) if model is not None else None

    def add(self, match: Match) -> Match:
        model = _match_to_orm(match)
        self._session.add(model)
        self._session.flush()
        return _match_to_domain(model)

    def save(self, match: Match) -> Match:
        model = self._session.get(MatchModel, match.id) if match.id is not None else None
        if model is None:
            raise ValueError(f"Match with id {match.id} not found")
        for field, value in {
            "match_id": match.match_id,
            "start_time": match.start_time,
            "duration_seconds": match.duration_seconds,
            "game_mode": match.game_mode,
            "lobby_type": match.lobby_type,
            "radiant_win": match.radiant_win,
            "radiant_score": match.radiant_score,
            "dire_score": match.dire_score,
            "patch": match.patch,
            "region": match.region,
            "radiant_team_id": match.radiant_team_id,
            "dire_team_id": match.dire_team_id,
            "raw_match": match.raw_match,
        }.items():
            setattr(model, field, value)
        self._session.flush()
        return _match_to_domain(model)


class SqlAlchemyHeroRepository(HeroRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, hero_id: HeroId) -> Hero | None:
        model = self._session.get(HeroModel, hero_id)
        return _hero_to_domain(model) if model is not None else None

    def get_by_external_id(self, hero_id: HeroId) -> Hero | None:
        model = self._session.execute(
            select(HeroModel).where(HeroModel.hero_id == hero_id)
        ).scalar_one_or_none()
        return _hero_to_domain(model) if model is not None else None

    def get_all_active(self) -> Sequence[Hero]:
        models = (
            self._session.execute(
                select(HeroModel).where(HeroModel.is_active == True)  # noqa: E712
            )
            .scalars()
            .all()
        )
        return [_hero_to_domain(m) for m in models]

    def add(self, hero: Hero) -> Hero:
        model = _hero_to_orm(hero)
        self._session.add(model)
        self._session.flush()
        return _hero_to_domain(model)

    def save(self, hero: Hero) -> Hero:
        model = self._session.get(HeroModel, hero.id) if hero.id is not None else None
        if model is None:
            raise ValueError(f"Hero with id {hero.id} not found")
        for field, value in {
            "hero_id": hero.hero_id,
            "name": hero.name,
            "localized_name": hero.localized_name,
            "primary_attr": hero.primary_attr,
            "attack_type": hero.attack_type,
            "roles": hero.roles,
            "legs": hero.legs,
            "is_active": hero.is_active,
            "raw_data": hero.raw_data,
        }.items():
            setattr(model, field, value)
        self._session.flush()
        return _hero_to_domain(model)


class SqlAlchemyItemRepository(ItemRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, item_id: ItemId) -> Item | None:
        model = self._session.get(ItemModel, item_id)
        return _item_to_domain(model) if model is not None else None

    def get_by_external_id(self, item_id: ItemId) -> Item | None:
        model = self._session.execute(
            select(ItemModel).where(ItemModel.item_id == item_id)
        ).scalar_one_or_none()
        return _item_to_domain(model) if model is not None else None

    def get_all(self) -> Sequence[Item]:
        models = self._session.execute(select(ItemModel)).scalars().all()
        return [_item_to_domain(m) for m in models]

    def add(self, item: Item) -> Item:
        model = _item_to_orm(item)
        self._session.add(model)
        self._session.flush()
        return _item_to_domain(model)

    def save(self, item: Item) -> Item:
        model = self._session.get(ItemModel, item.id) if item.id is not None else None
        if model is None:
            raise ValueError(f"Item with id {item.id} not found")
        for field, value in {
            "item_id": item.item_id,
            "name": item.name,
            "localized_name": item.localized_name,
            "cost": item.cost,
            "is_recipe": item.is_recipe,
            "in_secret_shop": item.in_secret_shop,
            "in_side_shop": item.in_side_shop,
            "raw_data": item.raw_data,
        }.items():
            setattr(model, field, value)
        self._session.flush()
        return _item_to_domain(model)


class SqlAlchemyPlayerMatchRepository(PlayerMatchRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, row_id: int) -> PlayerMatch | None:
        model = self._session.get(PlayerMatchModel, row_id)
        return _player_match_to_domain(model) if model is not None else None

    def get_by_match_and_slot(self, match_id: MatchId, player_slot: int) -> PlayerMatch | None:
        model = self._session.execute(
            select(PlayerMatchModel).where(
                PlayerMatchModel.match_id == match_id,
                PlayerMatchModel.player_slot == player_slot,
            )
        ).scalar_one_or_none()
        return _player_match_to_domain(model) if model is not None else None

    def list_by_match(self, match_id: MatchId) -> Sequence[PlayerMatch]:
        models = (
            self._session.execute(
                select(PlayerMatchModel).where(PlayerMatchModel.match_id == match_id)
            )
            .scalars()
            .all()
        )
        return [_player_match_to_domain(m) for m in models]

    def list_by_player(self, player_id: PlayerId) -> Sequence[PlayerMatch]:
        models = (
            self._session.execute(
                select(PlayerMatchModel).where(PlayerMatchModel.player_id == player_id)
            )
            .scalars()
            .all()
        )
        return [_player_match_to_domain(m) for m in models]

    def add(self, player_match: PlayerMatch) -> PlayerMatch:
        model = _player_match_to_orm(player_match)
        self._session.add(model)
        self._session.flush()
        return _player_match_to_domain(model)

    def save(self, player_match: PlayerMatch) -> PlayerMatch:
        model = self._session.get(PlayerMatchModel, player_match.id)
        if model is None:
            raise ValueError(f"PlayerMatch with id {player_match.id} not found")
        for field, value in {
            "match_id": player_match.match_id,
            "player_id": player_match.player_id,
            "account_id": player_match.account_id,
            "hero_id": player_match.hero_id,
            "player_slot": player_match.player_slot,
            "is_radiant": player_match.is_radiant,
            "win": player_match.win,
            "kills": player_match.kills,
            "deaths": player_match.deaths,
            "assists": player_match.assists,
            "gold_per_min": player_match.gold_per_min,
            "xp_per_min": player_match.xp_per_min,
            "last_hits": player_match.last_hits,
            "denies": player_match.denies,
            "hero_damage": player_match.hero_damage,
            "tower_damage": player_match.tower_damage,
            "hero_healing": player_match.hero_healing,
            "level": player_match.level,
            "item_0_id": player_match.item_0_id,
            "item_1_id": player_match.item_1_id,
            "item_2_id": player_match.item_2_id,
            "item_3_id": player_match.item_3_id,
            "item_4_id": player_match.item_4_id,
            "item_5_id": player_match.item_5_id,
            "item_neutral_id": player_match.item_neutral_id,
            "lane": player_match.lane,
            "role": player_match.role,
            "raw_player": player_match.raw_player,
        }.items():
            setattr(model, field, value)
        self._session.flush()
        return _player_match_to_domain(model)


class SqlAlchemyUnitOfWork:
    """Unit of work backed by a SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()


__all__ = [
    "SqlAlchemyHeroRepository",
    "SqlAlchemyItemRepository",
    "SqlAlchemyMatchRepository",
    "SqlAlchemyPlayerMatchRepository",
    "SqlAlchemyPlayerRepository",
    "SqlAlchemyUnitOfWork",
]
