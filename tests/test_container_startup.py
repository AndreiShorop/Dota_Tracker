"""Container startup and Alembic URL handling without a running database."""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

from dota_tracker.infrastructure.settings import load_settings
from dota_tracker.presentation.web import container


@pytest.fixture
def container_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_USER", "user@name")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pa%ss:@/$word?#")
    monkeypatch.setenv("POSTGRES_DB", "dota_tracker")
    monkeypatch.setenv("DB_HOST", "dota-postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://wrong:wrong@localhost:5433/wrong")


def test_container_url_migrations_and_server_order(
    container_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    events: list[str] = []

    def migrate(config: Config, revision: str) -> None:
        assert revision == "head"
        url = make_url(load_settings().database_url)
        assert (url.username, url.password) == ("user@name", "pa%ss:@/$word?#")
        assert (url.host, url.port, url.database) == ("dota-postgres", 5432, "dota_tracker")
        events.append("migrate")

    def start(program: str, args: list[str]) -> None:
        assert program == "uvicorn"
        assert args == [
            "uvicorn", "dota_tracker.presentation.web.app:app", "--host", "0.0.0.0",
            "--port", "8000",
        ]
        events.append("server")

    monkeypatch.setattr(container.command, "upgrade", migrate)
    monkeypatch.setattr(container.os, "execvp", start)
    container.main()
    assert events == ["migrate", "server"]


def test_failed_migration_does_not_start_server(
    container_environment: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    start = Mock()
    monkeypatch.setattr(container.os, "execvp", start)
    monkeypatch.setattr(container.command, "upgrade", Mock(side_effect=RuntimeError("migration")))
    with pytest.raises(RuntimeError, match="migration"):
        container.main()
    start.assert_not_called()


def test_missing_container_settings_fail_before_migration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DB_HOST", raising=False)
    migrate = Mock()
    monkeypatch.setattr(container.command, "upgrade", migrate)
    with pytest.raises(RuntimeError, match="DB_HOST"):
        container.main()
    migrate.assert_not_called()


def test_alembic_handles_percent_encoded_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    url = "postgresql+psycopg2://user:pa%25ss%40word@localhost:5433/dota_tracker"
    monkeypatch.setenv("DATABASE_URL", url)
    output = StringIO()
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"), output_buffer=output)
    command.upgrade(config, "head", sql=True)
    assert config.get_main_option("sqlalchemy.url") == url
    assert "CREATE TABLE" in output.getvalue()
