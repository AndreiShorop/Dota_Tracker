"""Request-scoped wiring for web application use cases."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.exc import SQLAlchemyError

from dota_tracker.application.use_cases import (
    DashboardUseCase,
    MatchDetailUseCase,
    SyncPlayerMatchesUseCase,
)
from dota_tracker.application.web_errors import (
    MatchDetailUnavailableError,
    StorageUnavailableError,
    SyncUnavailableError,
)
from dota_tracker.infrastructure.dashboard import SqlAlchemyDashboardReader
from dota_tracker.infrastructure.database import create_session
from dota_tracker.infrastructure.opendota.client import OpenDotaClient
from dota_tracker.infrastructure.opendota.exceptions import OpenDotaError
from dota_tracker.infrastructure.opendota.gateway import OpenDotaGateway
from dota_tracker.infrastructure.opendota.match_detail import (
    MatchCatalogCache,
    OpenDotaMatchDetailReader,
)
from dota_tracker.infrastructure.repositories import (
    SqlAlchemyHeroRepository,
    SqlAlchemyItemRepository,
    SqlAlchemyMatchRepository,
    SqlAlchemyPlayerMatchRepository,
    SqlAlchemyPlayerRepository,
    SqlAlchemyUnitOfWork,
)
from dota_tracker.infrastructure.settings import load_settings

_match_catalog_cache = MatchCatalogCache()


def match_detail_service() -> Iterator[MatchDetailUseCase]:
    """Provide match detail using a client closed when the request finishes."""
    try:
        settings = load_settings()
        with OpenDotaClient(
            base_url=settings.opendota_base_url,
            api_key=settings.opendota_api_key,
            timeout_seconds=settings.opendota_timeout_seconds,
            max_retries=settings.opendota_max_retries,
            rate_limit_rpm=settings.opendota_rate_limit_rpm,
        ) as client:
            yield MatchDetailUseCase(
                OpenDotaMatchDetailReader(client, _match_catalog_cache, settings.opendota_base_url)
            )
    except OpenDotaError as exc:
        raise MatchDetailUnavailableError from exc


def dashboard_service() -> Iterator[DashboardUseCase]:
    """Provide a dashboard use case with a session closed after each request."""
    try:
        with create_session() as session:
            yield DashboardUseCase(SqlAlchemyDashboardReader(session))
    except SQLAlchemyError as exc:
        raise StorageUnavailableError from exc


def sync_service() -> Iterator[SyncPlayerMatchesUseCase]:
    """Provide the existing sync workflow with isolated, automatically closed resources."""
    try:
        settings = load_settings()
        with (
            create_session(settings) as session,
            OpenDotaClient(
                base_url=settings.opendota_base_url,
                api_key=settings.opendota_api_key,
                timeout_seconds=settings.opendota_timeout_seconds,
                max_retries=settings.opendota_max_retries,
                rate_limit_rpm=settings.opendota_rate_limit_rpm,
            ) as client,
        ):
            yield SyncPlayerMatchesUseCase(
                gateway=OpenDotaGateway(client),
                player_repo=SqlAlchemyPlayerRepository(session),
                match_repo=SqlAlchemyMatchRepository(session),
                player_match_repo=SqlAlchemyPlayerMatchRepository(session),
                hero_repo=SqlAlchemyHeroRepository(session),
                item_repo=SqlAlchemyItemRepository(session),
                unit_of_work=SqlAlchemyUnitOfWork(session),
            )
    except SQLAlchemyError as exc:
        raise StorageUnavailableError from exc
    except OpenDotaError as exc:
        raise SyncUnavailableError from exc
