"""Dashboard projection and read-adapter tests."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateTable

from dota_tracker.infrastructure.dashboard import SqlAlchemyDashboardReader, hero_image_url
from dota_tracker.infrastructure.database import Base
from dota_tracker.infrastructure.models import Hero, Match, Player, PlayerMatch
from dota_tracker.shared.types import AccountId


@compiles(JSONB, "sqlite")
def _sqlite_jsonb(type_: JSONB, compiler: object, **kwargs: object) -> str:
    return "JSON"


def test_hero_image_url_rejects_untrusted_names() -> None:
    assert hero_image_url("npc_dota_hero_axe").endswith("/axe.png")  # type: ignore[union-attr]
    for name in (None, "axe", "npc_dota_hero_../secret", "npc_dota_hero_axe?foo=bar"):
        assert hero_image_url(name) is None


def test_read_adapter_joins_internal_keys_and_preserves_nulls() -> None:
    engine = create_engine("sqlite://")
    with engine.begin() as connection:
        for table in Base.metadata.sorted_tables:
            connection.execute(CreateTable(table))
    with Session(engine) as session:
        session.add_all([
            Player(id=10, account_id=42, persona_name="A", is_tracked=False),
            Player(id=11, account_id=99, persona_name="B", is_tracked=True),
            Hero(id=20, hero_id=2, name="npc_dota_hero_axe", localized_name="Axe"),
            Match(id=30, match_id=1234, start_time=datetime(2026, 1, 1, tzinfo=UTC)),
            Match(id=31, match_id=5678, start_time=datetime(2026, 2, 1, tzinfo=UTC)),
            PlayerMatch(id=1, match_id=30, player_id=10, account_id=42, hero_id=20,
                        player_slot=0, is_radiant=True, kills=3, deaths=2, assists=1),
            PlayerMatch(id=2, match_id=31, player_id=None, account_id=42, hero_id=20,
                        player_slot=0, is_radiant=False, kills=5, deaths=0, assists=2),
            PlayerMatch(id=3, match_id=31, player_id=11, account_id=99, hero_id=20,
                        player_slot=1, is_radiant=True, kills=9, deaths=0, assists=0),
        ])
        session.commit()
        reader = SqlAlchemyDashboardReader(session)
        assert [p.account_id for p in reader.list_players()] == [42, 99]
        dashboard = reader.get_dashboard(AccountId(42))
        assert dashboard is not None
        assert [m.match_id for m in dashboard.matches] == [5678, 1234]
        assert dashboard.matches[0].hero_id == 2
        assert dashboard.matches[0].hero_name == "Axe"
        assert dashboard.matches[0].win is None
        assert dashboard.matches[0].hero_damage is None
        assert reader.get_dashboard(AccountId(999)) is None
    engine.dispose()
