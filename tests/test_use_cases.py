"""Unit tests for application use cases with fake repositories/gateway."""

from __future__ import annotations

from dataclasses import replace
from typing import cast

from dota_tracker.application.dtos import (
    HeroDTO,
    ItemDTO,
    MatchDTO,
    PlayerDTO,
    SyncResult,
)
from dota_tracker.application.use_cases import SyncPlayerMatchesUseCase
from dota_tracker.domain.entities import Hero, Match, Player, PlayerMatch
from dota_tracker.domain.repositories import (
    HeroRepository,
    ItemRepository,
    MatchRepository,
    PlayerMatchRepository,
    PlayerRepository,
)
from dota_tracker.shared.types import AccountId, HeroId, MatchId, PlayerId


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_player(self, account_id: int) -> PlayerDTO | None:
        self.calls.append("get_player")
        return PlayerDTO(
            account_id=int(account_id),
            persona_name="TestPlayer",
            is_tracked=False,
        )

    def get_player_recent_matches(self, account_id: int, limit: int = 20) -> list[MatchDTO]:
        self.calls.append("get_player_recent_matches")
        return [
            MatchDTO(
                match_id=101,
                hero_id=1,
                player_slot=0,
                win=True,
                kills=5,
                deaths=2,
                assists=10,
                item_0_id=1,
            ),
            MatchDTO(
                match_id=102,
                hero_id=2,
                player_slot=1,
                win=False,
                kills=3,
                deaths=5,
                assists=8,
            ),
        ]

    def get_match(self, match_id: int) -> MatchDTO | None:
        return None

    def get_heroes(self) -> list[HeroDTO]:
        return [
            HeroDTO(hero_id=1, name="npc_dota_hero_axe", localized_name="Axe"),
            HeroDTO(hero_id=2, name="npc_dota_hero_invoker", localized_name="Invoker"),
        ]

    def get_items(self) -> list[ItemDTO]:
        return [ItemDTO(item_id=1, name="item_blink", localized_name="Blink Dagger", cost=2250)]


class FakePlayerRepo(PlayerRepository):
    def __init__(self) -> None:
        self.players: dict[int, Player] = {}
        self.added: list[Player] = []

    def add(self, player: Player) -> Player:
        player = replace(player, id=PlayerId(len(self.players) + 1))
        self.added.append(player)
        self.players[player.account_id] = player
        return player

    def save(self, player: Player) -> Player:
        self.players[player.account_id] = player
        return player

    def get_by_id(self, player_id: int) -> Player | None:
        return None

    def get_by_account_id(self, account_id: AccountId) -> Player | None:
        return self.players.get(int(account_id))

    def list_tracked(self) -> list[Player]:
        return list(self.players.values())


class FakeMatchRepo(MatchRepository):
    def __init__(self) -> None:
        self.matches: dict[int, Match] = {}
        self.added: list[Match] = []

    def add(self, match: Match) -> Match:
        match = replace(match, id=MatchId(len(self.matches) + 1))
        self.added.append(match)
        self.matches[match.match_id] = match
        return match

    def save(self, match: Match) -> Match:
        self.matches[match.match_id] = match
        return match

    def get_by_id(self, match_id: int) -> Match | None:
        return None

    def get_by_external_id(self, match_id: int) -> Match | None:
        return self.matches.get(match_id)


class FakePlayerMatchRepo(PlayerMatchRepository):
    def __init__(self) -> None:
        self.rows: dict[tuple[int, int], PlayerMatch] = {}
        self.added: list[PlayerMatch] = []

    def add(self, player_match: PlayerMatch) -> PlayerMatch:
        self.added.append(player_match)
        self.rows[(player_match.match_id, player_match.player_slot)] = player_match
        return player_match

    def save(self, player_match: PlayerMatch) -> PlayerMatch:
        self.rows[(player_match.match_id, player_match.player_slot)] = player_match
        return player_match

    def get_by_id(self, row_id: int) -> PlayerMatch | None:
        return None

    def get_by_match_and_slot(self, match_id: int, player_slot: int) -> PlayerMatch | None:
        return self.rows.get((match_id, player_slot))

    def list_by_match(self, match_id: int) -> list[PlayerMatch]:
        return [pm for (m, _), pm in self.rows.items() if m == match_id]

    def list_by_player(self, player_id: int) -> list[PlayerMatch]:
        return []


class FakeHeroRepo(HeroRepository):
    def __init__(self) -> None:
        self.heroes: dict[int, Hero] = {}

    def add(self, hero: Hero) -> Hero:
        hero = replace(hero, id=HeroId(len(self.heroes) + 1))
        self.heroes[hero.hero_id] = hero
        return hero

    def save(self, hero: Hero) -> Hero:
        self.heroes[hero.hero_id] = hero
        return hero

    def get_by_id(self, hero_id: int) -> Hero | None:
        return None

    def get_by_external_id(self, hero_id: int) -> Hero | None:
        return self.heroes.get(hero_id)

    def get_all_active(self) -> list[Hero]:
        return list(self.heroes.values())


class FakeItemRepo(ItemRepository):
    def __init__(self) -> None:
        self.items: dict[int, object] = {}

    def add(self, item: object) -> object:
        self.items[getattr(item, "item_id", 0)] = item
        return item

    def save(self, item: object) -> object:
        self.items[getattr(item, "item_id", 0)] = item
        return item

    def get_by_id(self, item_id: int) -> object:
        return self.items.get(item_id)

    def get_by_external_id(self, item_id: int) -> object:
        return self.items.get(item_id)

    def get_all(self) -> list[object]:
        return list(self.items.values())


class FakeUnitOfWork:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True


def make_use_case(
    gateway=None,
    player_repo=None,
    match_repo=None,
    pm_repo=None,
    hero_repo=None,
    item_repo=None,
    uow=None,
) -> SyncPlayerMatchesUseCase:
    return SyncPlayerMatchesUseCase(
        gateway=cast(object, gateway or FakeGateway()),
        player_repo=cast(object, player_repo or FakePlayerRepo()),
        match_repo=cast(object, match_repo or FakeMatchRepo()),
        player_match_repo=cast(object, pm_repo or FakePlayerMatchRepo()),
        hero_repo=cast(object, hero_repo or FakeHeroRepo()),
        item_repo=cast(object, item_repo or FakeItemRepo()),
        unit_of_work=uow,
    )


def test_sync_creates_player_and_matches():
    use_case = make_use_case()
    result = use_case.execute(AccountId(12345), limit=20)

    assert isinstance(result, SyncResult)
    assert result.account_id == 12345
    assert result.players_synced == 1
    assert result.matches_synced == 2
    assert result.player_matches_synced == 2


def test_sync_commits_unit_of_work():
    uow = FakeUnitOfWork()
    use_case = make_use_case(uow=uow)
    use_case.execute(AccountId(12345))
    assert uow.committed is True


def test_sync_raises_when_player_missing():
    gateway = FakeGateway()
    gateway.get_player = lambda account_id: None  # type: ignore[method-assign]
    use_case = make_use_case(gateway=gateway)
    try:
        use_case.execute(AccountId(999))
    except Exception as exc:
        from dota_tracker.domain.exceptions import PlayerNotFoundError

        assert isinstance(exc, PlayerNotFoundError)
    else:
        raise AssertionError("expected PlayerNotFoundError")
