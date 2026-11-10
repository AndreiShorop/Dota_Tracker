"""Unit tests for domain entities and value objects."""

from dota_tracker.domain.entities import Hero, Item, Match, MatchOutcome, PlayerMatch


def test_match_compute_outcome_radiant_win():
    match = Match(match_id=1, radiant_win=True)
    assert match.compute_outcome() == MatchOutcome.RADIANT_WIN


def test_match_compute_outcome_dire_win():
    match = Match(match_id=2, radiant_win=False)
    assert match.compute_outcome() == MatchOutcome.DIRE_WIN


def test_match_compute_outcome_unknown():
    match = Match(match_id=3, radiant_win=None)
    assert match.compute_outcome() == MatchOutcome.UNKNOWN


def test_player_match_kda_property():
    pm = PlayerMatch(
        match_id=1, hero_id=10, player_slot=0, is_radiant=True, kills=5, deaths=2, assists=10
    )
    assert pm.kda == (5, 2, 10)


def test_hero_defaults():
    hero = Hero(hero_id=1, name="npc_dota_hero_axe", localized_name="Axe")
    assert hero.is_active is True
    assert hero.roles is None


def test_item_defaults():
    item = Item(item_id=1, name="item_blink", localized_name="Blink Dagger", cost=2250)
    assert item.is_recipe is False
    assert item.in_secret_shop is False
