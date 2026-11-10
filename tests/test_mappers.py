"""Unit tests for OpenDota mappers."""

from dota_tracker.infrastructure.opendota.mappers import map_hero, map_item, map_match, map_player
from dota_tracker.infrastructure.opendota.models import (
    OpenDotaHero,
    OpenDotaItem,
    OpenDotaMatch,
    OpenDotaPlayer,
    OpenDotaPlayerProfile,
)


def test_map_player():
    dto = OpenDotaPlayer(
        account_id=42,
        profile=OpenDotaPlayerProfile(
            personaname="TestPlayer",
            steamid="76561198000000000",
            avatarfull="http://avatar",
            profileurl="http://profile",
            loccountrycode="US",
            last_match_time=1000000000,
        ),
    )
    result = map_player(dto)
    assert result.account_id == 42
    assert result.persona_name == "TestPlayer"
    assert result.steam_id == "76561198000000000"
    assert result.avatar_url == "http://avatar"
    assert result.is_tracked is False


def test_match_match():
    dto = OpenDotaMatch(
        match_id=777,
        start_time=1000000000,
        duration=1800,
        radiant_win=True,
        hero_id=1,
        player_slot=0,
        win=True,
        kills=5,
        item_0=1,
        item_1=2,
    )
    result = map_match(dto)
    assert result.match_id == 777
    assert result.duration_seconds == 1800
    assert result.radiant_win is True
    assert result.hero_id == 1
    assert result.player_slot == 0
    assert result.win is True
    assert result.kills == 5
    assert result.item_0_id == 1
    assert result.item_1_id == 2


def test_map_hero():
    dto = OpenDotaHero(id=1, name="npc_dota_hero_axe", localized_name="Axe", primary_attr="str")
    result = map_hero(dto)
    assert result.hero_id == 1
    assert result.name == "npc_dota_hero_axe"
    assert result.localized_name == "Axe"
    assert result.primary_attr == "str"


def test_map_item():
    dto = OpenDotaItem(
        id=1, name="item_blink", localized_name="Blink Dagger", cost=2250, is_recipe=False
    )
    result = map_item(dto)
    assert result.item_id == 1
    assert result.localized_name == "Blink Dagger"
    assert result.cost == 2250
    assert result.is_recipe is False
