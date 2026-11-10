"""API tests using application-level fakes rather than live services."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from dota_tracker.application.dtos import (
    DashboardMatch,
    DashboardPlayer,
    PlayerDashboard,
    SyncResult,
)
from dota_tracker.application.use_cases import DashboardUseCase
from dota_tracker.application.web_errors import StorageUnavailableError, SyncUnavailableError
from dota_tracker.domain.exceptions import PlayerNotFoundError
from dota_tracker.presentation.web import composition
from dota_tracker.presentation.web.app import create_app
from dota_tracker.presentation.web.composition import dashboard_service, sync_service
from dota_tracker.shared.types import AccountId


class FakeReader:
    def list_players(self) -> list[DashboardPlayer]:
        return [DashboardPlayer(account_id=42, persona_name="Player", avatar_url=None)]

    def get_dashboard(self, account_id: AccountId) -> PlayerDashboard | None:
        if account_id != 42:
            return None
        return PlayerDashboard(
            player=self.list_players()[0],
            matches=[DashboardMatch(
                match_id=1234,
                start_time=datetime(2026, 1, 1, tzinfo=UTC),
                duration_seconds=1800,
                hero_id=2,
                hero_name="Axe",
                hero_image=None,
                win=None,
                kills=3,
                deaths=2,
                assists=10,
                gold_per_min=None,
                xp_per_min=None,
                last_hits=None,
                hero_damage=None,
                tower_damage=None,
                hero_healing=None,
                is_radiant=True,
                game_mode=None,
            )],
        )


class FakeSync:
    def __init__(self) -> None:
        self.calls: list[tuple[int, int]] = []

    def execute(self, account_id: AccountId, limit: int) -> SyncResult:
        self.calls.append((account_id, limit))
        return SyncResult(account_id=account_id, players_synced=1, matches_synced=2,
                          player_matches_synced=2)


@pytest.fixture
def api() -> tuple[TestClient, FakeSync]:
    app = create_app()
    sync = FakeSync()
    app.dependency_overrides[dashboard_service] = lambda: DashboardUseCase(FakeReader())
    app.dependency_overrides[sync_service] = lambda: sync
    return TestClient(app), sync


def test_players_dashboard_and_missing_player(api: tuple[TestClient, FakeSync]) -> None:
    client, _ = api
    assert client.get("/api/players").json() == {
        "players": [{"account_id": 42, "persona_name": "Player", "avatar_url": None}]
    }
    response = client.get("/api/players/42/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["player"]["account_id"] == 42
    assert data["matches"][0]["match_id"] == 1234
    assert data["matches"][0]["start_time"] == "2026-01-01T00:00:00Z"
    assert data["matches"][0]["win"] is None
    assert data["synced_at"] is None
    assert client.get("/api/players/43/dashboard").status_code == 404


def test_sync_and_validation(api: tuple[TestClient, FakeSync]) -> None:
    client, sync = api
    assert client.post("/api/players/42/sync").json() == {
        "players_synced": 1, "matches_synced": 2, "player_matches_synced": 2,
    }
    assert client.post("/api/players/42/sync?limit=100").status_code == 200
    for path in ("/api/players/0/dashboard", "/api/players/-1/dashboard",
                 "/api/players/4294967296/dashboard", "/api/players/nope/dashboard",
                 "/api/players/42/sync?limit=0", "/api/players/42/sync?limit=101"):
        response = client.post(path) if "/sync" in path else client.get(path)
        assert response.status_code == 422
    assert sync.calls == [(42, 50), (42, 100)]


def test_sync_rejects_cross_origin_requests(api: tuple[TestClient, FakeSync]) -> None:
    client, sync = api
    response = client.post("/api/players/42/sync", headers={"Origin": "https://example.com"})
    assert response.status_code == 403
    assert sync.calls == []
    same_origin = client.post("/api/players/42/sync", headers={"Origin": "http://testserver"})
    assert same_origin.status_code == 200


@pytest.mark.parametrize("error,status", [
    (StorageUnavailableError("secret db url"), 503),
    (SyncUnavailableError("secret api key"), 502),
])
def test_safe_error_response(error: Exception, status: int) -> None:
    app = create_app()

    def fail() -> None:
        raise error

    app.dependency_overrides[dashboard_service] = fail
    response = TestClient(app).get("/api/players")
    assert response.status_code == status
    assert "secret" not in response.text
    assert response.headers["content-type"].startswith("application/json")


def test_database_failure_is_redacted_and_session_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    session.__enter__.return_value = session
    session.scalars.side_effect = OperationalError("secret query", {}, Exception("secret"))
    monkeypatch.setattr(composition, "create_session", lambda *args: session)
    response = TestClient(create_app()).get("/api/players")
    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
    assert "secret" not in response.text
    session.__exit__.assert_called_once()


def test_sync_closes_client_and_session_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock()
    session.__enter__.return_value = session
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.side_effect = OperationalError("secret query", {}, Exception("secret"))
    monkeypatch.setattr(composition, "create_session", lambda *args: session)
    monkeypatch.setattr(composition, "OpenDotaClient", lambda **kwargs: client)
    response = TestClient(create_app()).post("/api/players/42/sync")
    assert response.status_code == 503
    assert "secret" not in response.text
    client.__exit__.assert_called_once()
    session.__exit__.assert_called_once()


def test_sync_closes_resources_on_success_and_missing_player(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = MagicMock()
    session.__enter__.return_value = session
    client = MagicMock()
    client.__enter__.return_value = client
    use_case = MagicMock()
    use_case.execute.return_value = SyncResult(account_id=42, players_synced=1)
    monkeypatch.setattr(composition, "create_session", lambda *args: session)
    monkeypatch.setattr(composition, "OpenDotaClient", lambda **kwargs: client)
    monkeypatch.setattr(composition, "SyncPlayerMatchesUseCase", lambda **kwargs: use_case)
    api = TestClient(create_app())
    assert api.post("/api/players/42/sync").status_code == 200
    use_case.execute.side_effect = PlayerNotFoundError("provider details")
    response = api.post("/api/players/42/sync")
    assert response.status_code == 404
    assert response.json() == {"detail": "Player not found"}
    assert client.__exit__.call_count == 2
    assert session.__exit__.call_count == 2


