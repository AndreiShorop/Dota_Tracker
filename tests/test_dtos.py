"""Tests for application DTOs validation."""

from pydantic import ValidationError

from dota_tracker.application.dtos import MatchDTO, PlayerDTO


def test_player_dto_valid():
    dto = PlayerDTO(account_id=42, persona_name="Player")
    assert dto.account_id == 42


def test_match_dto_negative_kills_rejected():
    try:
        MatchDTO(match_id=1, kills=-1)
    except ValidationError:
        pass
    else:
        raise AssertionError("expected ValidationError for negative kills")


def test_match_dto_defaults():
    dto = MatchDTO(match_id=1)
    assert dto.kills is None
    assert dto.hero_id is None
