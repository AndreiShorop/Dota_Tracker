"""Regression tests for paginated OpenDota history and atomic synchronization."""

from __future__ import annotations

from collections.abc import Callable, Iterator

import httpx
import pytest

from dota_tracker.application.dtos import MatchDTO
from dota_tracker.infrastructure.opendota.client import OpenDotaClient
from dota_tracker.infrastructure.opendota.exceptions import (
    OpenDotaRateLimitError,
    OpenDotaResponseValidationError,
)
from dota_tracker.infrastructure.opendota.gateway import OpenDotaGateway
from dota_tracker.shared.types import AccountId
from test_use_cases import (
    FakeGateway,
    FakeMatchRepo,
    FakePlayerMatchRepo,
    FakeUnitOfWork,
    make_use_case,
)


def gateway_for(
    handler: Callable[[httpx.Request], httpx.Response], retries: int = 0
) -> OpenDotaGateway:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OpenDotaGateway(OpenDotaClient(
        "https://api.opendota.com/api", client=client, max_retries=retries, rate_limit_rpm=60000
    ))


def test_full_history_paginates_by_offset_and_preserves_timestamp_ties() -> None:
    calls: list[tuple[int, int]] = []
    matches = [{"match_id": i, "start_time": 1700000000} for i in range(250, 0, -1)]

    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["significant"] == "0"
        offset, limit = int(params["offset"]), int(params["limit"])
        calls.append((offset, limit))
        return httpx.Response(200, json=matches[offset:offset + limit])

    gateway = gateway_for(handler)
    result = list(gateway.iter_player_matches(AccountId(42), None))
    assert [match.match_id for match in result] == list(range(250, 0, -1))
    assert calls == [(0, 100), (100, 100), (200, 100), (250, 100)]


def test_limit_above_100_and_short_pages() -> None:
    calls: list[tuple[int, int]] = []
    matches = [{"match_id": i} for i in range(180, 0, -1)]

    def handler(request: httpx.Request) -> httpx.Response:
        offset, limit = int(request.url.params["offset"]), int(request.url.params["limit"])
        calls.append((offset, limit))
        return httpx.Response(200, json=matches[offset:offset + min(limit, 60)])

    result = gateway_for(handler).get_player_recent_matches(AccountId(42), limit=125)
    assert [match.match_id for match in result] == list(range(180, 55, -1))
    assert calls == [(0, 100), (60, 65), (120, 5)]


@pytest.mark.parametrize("count", [0, 100, 200])
def test_full_history_stops_after_empty_page(count: int) -> None:
    offsets: list[int] = []
    matches = [{"match_id": i} for i in range(count, 0, -1)]

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["offset"])
        offsets.append(offset)
        return httpx.Response(200, json=matches[offset:offset + 100])

    assert len(list(gateway_for(handler).iter_player_matches(AccountId(1), None))) == count
    assert offsets == list(range(0, count + 1, 100))


def test_duplicate_overlap_is_not_counted_and_repeated_pages_fail() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["offset"])
        pages = {0: [5, 4], 2: [4, 3], 4: [2, 1], 6: []}
        return httpx.Response(200, json=[{"match_id": value} for value in pages[offset]])

    result = gateway_for(handler).iter_player_matches(AccountId(1), None)
    assert [m.match_id for m in result] == [5, 4, 3, 2, 1]

    def repeated(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"match_id": 1}])

    with pytest.raises(OpenDotaResponseValidationError, match="no progress"):
        list(gateway_for(repeated).iter_player_matches(AccountId(1), None))


@pytest.mark.parametrize(
    "payload", [{"error": "bad"}, [None], [{"match_id": 0}], [{"match_id": 1}, {"match_id": 2}]]
)
def test_invalid_or_unordered_pages_fail(payload: object) -> None:
    gateway = gateway_for(lambda request: httpx.Response(200, json=payload))
    with pytest.raises(OpenDotaResponseValidationError):
        list(gateway.iter_player_matches(AccountId(1), None))


@pytest.mark.parametrize("account_id,limit", [(0, 1), (4294967296, 1), (1, 0), (1, -1), (1, True)])
def test_invalid_boundaries(account_id: int, limit: int) -> None:
    gateway = gateway_for(lambda request: httpx.Response(200, json=[]))
    with pytest.raises(ValueError):
        list(gateway.iter_player_matches(AccountId(account_id), limit))


def test_retries_429_on_later_page_and_fails_after_retry_budget() -> None:
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["offset"])
        calls.append(offset)
        if offset == 0:
            return httpx.Response(200, json=[{"match_id": 2}])
        if calls.count(offset) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json=[])

    result = gateway_for(handler, retries=1).iter_player_matches(AccountId(1), None)
    assert [m.match_id for m in result] == [2]
    assert calls == [0, 1, 1]

    limited = gateway_for(
        lambda request: httpx.Response(429, headers={"Retry-After": "0"}), retries=1
    )
    with pytest.raises(OpenDotaRateLimitError):
        list(limited.iter_player_matches(AccountId(1), None))


def test_sync_rolls_back_after_later_page_failure() -> None:
    class FailingGateway(FakeGateway):
        def iter_player_matches(
            self, account_id: int, limit: int | None = 20
        ) -> Iterator[MatchDTO]:
            yield MatchDTO(match_id=1, hero_id=1, player_slot=0)
            raise OpenDotaRateLimitError("rate limit")

    uow = FakeUnitOfWork()
    use_case = make_use_case(gateway=FailingGateway(), uow=uow)
    with pytest.raises(OpenDotaRateLimitError):
        use_case.execute(AccountId(42), limit=None)
    assert uow.rolled_back and not uow.committed


def test_sync_preserves_existing_richer_data() -> None:
    from dota_tracker.domain.entities import Match, PlayerMatch
    from dota_tracker.shared.types import HeroId, ItemId, MatchId

    match_repo = FakeMatchRepo()
    match_repo.matches[101] = Match(
        id=MatchId(1), match_id=MatchId(101), radiant_score=42, raw_match={"detailed": True}
    )
    pm_repo = FakePlayerMatchRepo()
    pm_repo.rows[(1, 0)] = PlayerMatch(
        id=5, match_id=MatchId(1), hero_id=HeroId(1), player_slot=0, is_radiant=True,
        item_0_id=ItemId(99), hero_damage=1234, raw_player={"detailed": True}
    )
    use_case = make_use_case(match_repo=match_repo, pm_repo=pm_repo)
    use_case.execute(AccountId(42), limit=None)
    assert match_repo.matches[101].radiant_score == 42
    assert match_repo.matches[101].raw_match == {"detailed": True}
    assert pm_repo.rows[(1, 0)].item_0_id == ItemId(99)
    assert pm_repo.rows[(1, 0)].hero_damage == 1234
    assert pm_repo.rows[(1, 0)].raw_player == {"detailed": True}


def test_repeated_full_sync_updates_instead_of_duplicating() -> None:
    matches, player_matches = FakeMatchRepo(), FakePlayerMatchRepo()
    use_case = make_use_case(match_repo=matches, pm_repo=player_matches)
    first = use_case.execute(AccountId(42), limit=None)
    second = use_case.execute(AccountId(42), limit=None)
    assert first.matches_synced == second.matches_synced == 2
    assert len(matches.matches) == len(matches.added) == 2
    assert len(player_matches.rows) == len(player_matches.added) == 2
