"""Match detail API and OpenDota adapter tests without external services."""

from __future__ import annotations

from collections.abc import Callable
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from dota_tracker.application.dtos import MatchDetailPlayer
from dota_tracker.application.use_cases import MatchDetailUseCase
from dota_tracker.domain.exceptions import MatchNotFoundError
from dota_tracker.infrastructure.opendota.client import OpenDotaClient
from dota_tracker.infrastructure.opendota.exceptions import (
    OpenDotaResponseValidationError,
    OpenDotaUnavailableError,
)
from dota_tracker.infrastructure.opendota.match_detail import (
    MatchCatalogCache,
    OpenDotaMatchDetailReader,
)
from dota_tracker.presentation.web import composition
from dota_tracker.presentation.web.app import create_app
from dota_tracker.presentation.web.composition import match_detail_service

MATCH = {
    "match_id": 7000000000,
    "start_time": 1675435535,
    "duration": 1604,
    "radiant_win": False,
    "radiant_score": 33,
    "dire_score": 53,
    "players": [
        {"account_id": 42, "player_slot": 0, "hero_id": 2, "personaname": "Player",
         "kills": 0, "deaths": 2, "assists": 3, "gold_per_min": 400,
         "xp_per_min": 500, "last_hits": 50, "hero_damage": 9000,
         "tower_damage": 300, "hero_healing": 0, "level": 20,
         "item_0": 1, "item_1": 0, "item_2": None, "backpack_0": 2,
         "item_neutral": 3, "item_neutral2": 9999, "purchase": {"tango": 99},
         "purchase_log": [{"time": -89, "key": "blink"},
                          {"time": -89, "key": "recipe_blink"},
                          {"time": -89, "key": "blink"},
                          {"time": 5, "key": "no_id"},
                          {"time": 6, "key": "unknown_item"},
                          {"time": 7, "key": "unsafe"}]},
        {"account_id": None, "player_slot": 128, "hero_id": 999, "name": "Anonymous",
         "kills": None, "item_0": 2, "purchase_log": []},
        {"account_id": 4294967295, "player_slot": None, "hero_id": None},
    ],
}
HEROES = {"2": {"id": 2, "localized_name": "Axe",
                 "img": "/apps/dota2/images/dota_react/heroes/axe.png?x=1"}}
ITEMS = {
    "blink": {"id": 1, "dname": "Blink Dagger",
              "img": "/apps/dota2/images/dota_react/items/blink.png?t=1"},
    "recipe_blink": {"id": 2, "dname": "Recipe",
                     "img": "/apps/dota2/images/dota_react/items/recipe.png?t=1"},
    "neutral": {"id": 3, "dname": "Neutral", "img": "//evil.example/item.png"},
    "no_id": {"dname": "Unknown"},
    "unsafe": {"dname": "<img src=x onerror=alert(1)>",
               "img": "https://evil.example/item.png"},
}


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> OpenDotaClient:
    """Construct an isolated HTTP client using a mocked provider."""
    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenDotaClient("https://example.test/api", client=http_client,
                          rate_limit_rpm=600000, max_retries=0)


def test_full_api_contract_and_catalog_cache() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        payloads = {"/api/matches/7000000000": MATCH, "/api/constants/heroes": HEROES,
                    "/api/constants/items": ITEMS}
        return httpx.Response(200, json=payloads[request.url.path])

    with make_client(handler) as provider:
        reader = OpenDotaMatchDetailReader(provider, MatchCatalogCache(), "provider")
        app = create_app()
        app.dependency_overrides[match_detail_service] = lambda: MatchDetailUseCase(reader)
        api = TestClient(app)
        response = api.get("/api/matches/7000000000")
        assert response.status_code == 200
        data = response.json()
        assert set(data) == {"match_id", "start_time", "duration_seconds", "radiant_win",
                             "radiant_score", "dire_score", "players"}
        assert data["start_time"] == "2023-02-03T14:45:35Z"
        assert data["duration_seconds"] == 1604
        radiant, dire, unknown = data["players"]
        assert set(radiant) == {"account_id", "player_slot", "hero_id", "hero_name",
                                "hero_image", "persona_name", "win", "kills", "deaths",
                                "assists", "gold_per_min", "xp_per_min", "last_hits",
                                "hero_damage", "tower_damage", "hero_healing", "level", "items",
                                "purchase_log"}
        assert radiant["hero_name"] == "Axe"
        assert radiant["hero_image"].endswith("/heroes/axe.png")
        assert radiant["win"] is False and dire["win"] is True and unknown["win"] is None
        assert radiant["kills"] == 0 and radiant["hero_healing"] == 0
        assert dire["kills"] is None and dire["hero_name"] is None
        assert unknown["account_id"] is None and unknown["items"] == []
        assert dire["purchase_log"] == [] and unknown["purchase_log"] is None
        assert radiant["purchase_log"] == [
            {"time": -89, "key": "blink", "name": "Blink Dagger", "image":
             "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/blink.png"},
            {"time": -89, "key": "recipe_blink", "name": "Recipe", "image":
             "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/recipe.png"},
            {"time": -89, "key": "blink", "name": "Blink Dagger", "image":
             "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/blink.png"},
            {"time": 5, "key": "no_id", "name": "Unknown", "image": None},
            {"time": 6, "key": "unknown_item", "name": None, "image": None},
            {"time": 7, "key": "unsafe", "name": None, "image": None},
        ]
        assert MatchDetailPlayer.model_validate(
            {key: value for key, value in unknown.items() if key != "purchase_log"}
        ).purchase_log is None
        assert radiant["items"] == [
            {"slot": 0, "id": 1, "name": "Blink Dagger", "image":
             "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/blink.png"},
            {"slot": 6, "id": 2, "name": "Recipe", "image":
             "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/recipe.png"},
            {"slot": 10, "id": 3, "name": "Neutral", "image": None},
            {"slot": 11, "id": 9999, "name": None, "image": None},
        ]
        assert api.get("/api/matches/7000000000").status_code == 200
        assert calls == ["/api/matches/7000000000", "/api/constants/heroes",
                         "/api/constants/items", "/api/matches/7000000000"]


@pytest.mark.parametrize("body,status", [(None, 200), ({"error": "missing"}, 404)])
def test_missing_match_never_requests_catalog(body: object, status: int) -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        if body is None:
            return httpx.Response(
                status, content=b"null", headers={"content-type": "application/json"}
            )
        return httpx.Response(status, json=body)

    with make_client(handler) as client:
        reader = OpenDotaMatchDetailReader(client, MatchCatalogCache(), "provider")
        with pytest.raises(MatchNotFoundError):
            MatchDetailUseCase(reader).execute(123)
    assert calls == ["/api/matches/123"]


@pytest.mark.parametrize("purchase_log", [
    {}, "invalid", [None], [{}], [{"time": None, "key": "blink"}],
    [{"time": True, "key": "blink"}], [{"time": 1.5, "key": "blink"}],
    [{"time": "1", "key": "blink"}], [{"time": 1}],
    [{"time": 1, "key": ""}], [{"time": 1, "key": 5}],
    [{"time": 1, "key": "<script>"}], [{"time": 1, "key": "a" * 129}],
])
def test_invalid_purchase_log_returns_sanitized_502(
    purchase_log: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "match_id": 123, "players": [{"purchase_log": purchase_log}],
        })

    with make_client(handler) as provider:
        monkeypatch.setattr(composition, "OpenDotaClient", lambda **kwargs: provider)
        response = TestClient(create_app()).get("/api/matches/123")
    assert response.status_code == 502
    assert response.json() == {"detail": "Match detail service unavailable"}


def test_explicit_null_purchase_log_is_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "/matches/" in request.url.path:
            return httpx.Response(200, json={
                "match_id": 123, "players": [{"purchase_log": None, "purchase": {"blink": 1}}],
            })
        return httpx.Response(200, json=HEROES if request.url.path.endswith("heroes") else ITEMS)

    with make_client(handler) as client:
        result = OpenDotaMatchDetailReader(client, MatchCatalogCache(), "provider")
        detail = result.get_match_detail(123)
    assert detail is not None
    assert detail.players[0].purchase_log is None


@pytest.mark.parametrize("payload", [[], {"match_id": 123},
                                     {"match_id": 123, "players": [{"kills": -1}]},
                                     {"match_id": 124, "players": []}])
def test_invalid_match_payload_rejected(payload: object) -> None:
    with make_client(lambda request: httpx.Response(200, json=payload)) as client:
        reader = OpenDotaMatchDetailReader(client, MatchCatalogCache(), "provider")
        with pytest.raises(OpenDotaResponseValidationError):
            reader.get_match_detail(123)


def test_invalid_json_and_catalog_are_rejected() -> None:
    with make_client(lambda request: httpx.Response(200, text="not json")) as client:
        reader = OpenDotaMatchDetailReader(client, MatchCatalogCache(), "provider")
        with pytest.raises(OpenDotaResponseValidationError):
            reader.get_match_detail(123)

    def handler(request: httpx.Request) -> httpx.Response:
        if "/matches/" in request.url.path:
            return httpx.Response(200, json={"match_id": 123, "players": []})
        return httpx.Response(200, json=[])

    with make_client(handler) as client:
        reader = OpenDotaMatchDetailReader(client, MatchCatalogCache(), "provider")
        with pytest.raises(OpenDotaResponseValidationError):
            reader.get_match_detail(123)


def test_catalog_expiry_and_failed_refresh_are_not_cached() -> None:
    calls: list[str] = []
    fail_items = True

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal fail_items
        calls.append(request.url.path)
        if request.url.path.endswith("/heroes"):
            return httpx.Response(200, json=HEROES)
        if fail_items:
            fail_items = False
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=ITEMS)

    with make_client(handler) as client:
        cache = MatchCatalogCache(ttl_seconds=0)
        with pytest.raises(OpenDotaResponseValidationError):
            cache.get(client, "provider")
        cache.get(client, "provider")
        cache.get(client, "provider")
    assert calls == ["/api/constants/heroes", "/api/constants/items"] * 3


def test_missing_outcome_remains_unknown() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "/matches/" in request.url.path:
            return httpx.Response(200, json={
                "match_id": 123,
                "radiant_win": None,
                "players": [{"player_slot": 0}, {"player_slot": 128}],
            })
        return httpx.Response(200, json=HEROES if request.url.path.endswith("heroes") else ITEMS)

    with make_client(handler) as client:
        detail = OpenDotaMatchDetailReader(client, MatchCatalogCache(), "provider")
        result = detail.get_match_detail(123)
    assert result is not None
    assert [player.win for player in result.players] == [None, None]


def test_api_invalid_ids_missing_and_provider_failure_cleanup(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.side_effect = OpenDotaUnavailableError("secret api key")
    monkeypatch.setattr(composition, "OpenDotaClient", lambda **kwargs: client)
    api = TestClient(create_app())
    for match_id in ("0", "-1", "abc", "9223372036854775808"):
        assert api.get(f"/api/matches/{match_id}").status_code == 422
    client.get.assert_not_called()
    response = api.get("/api/matches/123")
    assert response.status_code == 502
    assert response.json() == {"detail": "Match detail service unavailable"}
    assert "secret" not in response.text
    assert client.__exit__.call_count >= 1

    client.reset_mock()
    client.__enter__.return_value = client
    client.get.side_effect = None
    client.get.return_value.json.return_value = None
    response = api.get("/api/matches/123")
    assert response.status_code == 404
    assert response.json() == {"detail": "Match not found"}
    client.__exit__.assert_called_once()


def test_client_closed_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    client.__enter__.return_value = client
    client.get.return_value.json.return_value = {"match_id": 123, "players": []}
    monkeypatch.setattr(composition, "OpenDotaClient", lambda **kwargs: client)
    cache = MagicMock()
    cache.get.return_value = ({}, {})
    monkeypatch.setattr(composition, "_match_catalog_cache", cache)
    response = TestClient(create_app()).get("/api/matches/123")
    assert response.status_code == 200
    client.__exit__.assert_called_once()
