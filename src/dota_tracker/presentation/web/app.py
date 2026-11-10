"""FastAPI controllers for the local interactive dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi import Path as PathParam
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from dota_tracker.application.dtos import DashboardPlayer, MatchDetail, PlayerDashboard
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
from dota_tracker.domain.exceptions import MatchNotFoundError, PlayerNotFoundError
from dota_tracker.presentation.web.composition import (
    dashboard_service,
    match_detail_service,
    sync_service,
)
from dota_tracker.shared.types import AccountId

AccountPath = Annotated[int, PathParam(ge=1, le=4294967295)]
MatchPath = Annotated[int, PathParam(ge=1, le=9223372036854775807)]
SyncLimit = Annotated[int, Query(ge=1, le=2147483647)]
DashboardDependency = Annotated[DashboardUseCase, Depends(dashboard_service)]
SyncDependency = Annotated[SyncPlayerMatchesUseCase, Depends(sync_service)]
MatchDetailDependency = Annotated[MatchDetailUseCase, Depends(match_detail_service)]


class PlayersResponse(BaseModel):
    """Stored player list response."""

    players: list[DashboardPlayer]


class SyncResponse(BaseModel):
    """Counts of records processed by the sync workflow."""

    players_synced: int
    matches_synced: int
    player_matches_synced: int


def create_app() -> FastAPI:
    """Create the API and mount the independently built static frontend."""
    app = FastAPI(title="Dota Tracker")

    @app.exception_handler(PlayerNotFoundError)
    async def player_not_found(request: Request, exc: PlayerNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Player not found"})

    @app.exception_handler(MatchNotFoundError)
    async def match_not_found(request: Request, exc: MatchNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Match not found"})

    @app.exception_handler(MatchDetailUnavailableError)
    async def match_unavailable(
        request: Request, exc: MatchDetailUnavailableError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": "Match detail service unavailable"})

    @app.exception_handler(StorageUnavailableError)
    async def storage_unavailable(request: Request, exc: StorageUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    @app.exception_handler(SyncUnavailableError)
    async def sync_unavailable(request: Request, exc: SyncUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": "Sync service unavailable"})

    @app.get("/api/players", response_model=PlayersResponse)
    def list_players(service: DashboardDependency) -> PlayersResponse:
        return PlayersResponse(players=service.list_players())

    @app.get("/api/players/{account_id}/dashboard", response_model=PlayerDashboard)
    def dashboard(account_id: AccountPath, service: DashboardDependency) -> PlayerDashboard:
        return service.get_dashboard(AccountId(account_id))

    @app.get("/api/matches/{match_id}", response_model=MatchDetail)
    def match_detail(match_id: MatchPath, service: MatchDetailDependency) -> MatchDetail:
        return service.execute(match_id)

    @app.post("/api/players/{account_id}/sync", response_model=SyncResponse)
    def sync(
        account_id: AccountPath,
        service: SyncDependency,
        request: Request,
        limit: SyncLimit = 50,
        all_matches: bool = False,
    ) -> SyncResponse:
        origin = request.headers.get("origin")
        if origin is not None and origin != str(request.base_url).rstrip("/"):
            raise HTTPException(status_code=403, detail="Cross-origin sync is not allowed")
        result = service.execute(AccountId(account_id), limit=None if all_matches else limit)
        return SyncResponse(
            players_synced=result.players_synced,
            matches_synced=result.matches_synced,
            player_matches_synced=result.player_matches_synced,
        )

    static_dir = Path(__file__).parent / "static"
    app.mount("/", StaticFiles(directory=static_dir, html=True, check_dir=False), name="static")
    return app


app = create_app()
