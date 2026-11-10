"""Application entry point (CLI)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dota_tracker.analytics.charts import StatsCharts
from dota_tracker.analytics.stats import StatsCalculator
from dota_tracker.application.use_cases import SyncPlayerMatchesUseCase
from dota_tracker.domain.repositories import (
    HeroRepository,
    ItemRepository,
    MatchRepository,
    PlayerMatchRepository,
    PlayerRepository,
)
from dota_tracker.infrastructure.database import create_session, get_engine
from dota_tracker.infrastructure.logging import setup_logging
from dota_tracker.infrastructure.opendota.client import OpenDotaClient
from dota_tracker.infrastructure.opendota.gateway import OpenDotaGateway
from dota_tracker.infrastructure.repositories import (
    SqlAlchemyHeroRepository,
    SqlAlchemyItemRepository,
    SqlAlchemyMatchRepository,
    SqlAlchemyPlayerMatchRepository,
    SqlAlchemyPlayerRepository,
    SqlAlchemyUnitOfWork,
)
from dota_tracker.infrastructure.settings import load_settings
from dota_tracker.shared.logger import logger
from dota_tracker.shared.types import AccountId


def build_dependencies():
    settings = load_settings()
    setup_logging(log_level=settings.log_level)
    engine = get_engine(settings)
    session = create_session(settings)
    client = OpenDotaClient(
        base_url=settings.opendota_base_url,
        api_key=settings.opendota_api_key,
        timeout_seconds=settings.opendota_timeout_seconds,
        max_retries=settings.opendota_max_retries,
        rate_limit_rpm=settings.opendota_rate_limit_rpm,
    )
    gateway = OpenDotaGateway(client)
    player_repo: PlayerRepository = SqlAlchemyPlayerRepository(session)
    match_repo: MatchRepository = SqlAlchemyMatchRepository(session)
    pm_repo: PlayerMatchRepository = SqlAlchemyPlayerMatchRepository(session)
    hero_repo: HeroRepository = SqlAlchemyHeroRepository(session)
    item_repo: ItemRepository = SqlAlchemyItemRepository(session)
    uow = SqlAlchemyUnitOfWork(session)
    use_case = SyncPlayerMatchesUseCase(
        gateway=gateway,
        player_repo=player_repo,
        match_repo=match_repo,
        player_match_repo=pm_repo,
        hero_repo=hero_repo,
        item_repo=item_repo,
        unit_of_work=uow,
    )
    return settings, session, client, use_case, player_repo, pm_repo, hero_repo


def print_summary(summary):
    p = summary.player
    print("=" * 50)
    print(f"Player: {p.persona_name or 'Unknown'} (Account ID: {p.account_id})")
    if p.steam_id:
        print(f"Steam ID: {p.steam_id}")
    if p.country_code:
        print(f"Country: {p.country_code}")
    print("=" * 50)
    print(f"Total Games: {summary.total_games}")
    print(f"Wins: {summary.wins} | Losses: {summary.losses}")
    print(f"Winrate: {summary.winrate:.2f}%")
    print(f"Avg K/D/A: {summary.avg_kills:.1f}/{summary.avg_deaths:.1f}/{summary.avg_assists:.1f} (KDA {summary.avg_kda:.2f})")
    print("=" * 50)
    if summary.top_heroes:
        print("Top Heroes:")
        print(f"{'Hero':<25} {'Games':<7} {'W/L':<8} {'WR%':<8} {'KDA':<8}")
        print("-" * 50)
        for h in summary.top_heroes[:10]:
            print(f"{h.hero_name:<25} {h.games:<7} {h.wins}/{h.losses:<6} {h.winrate:<7.1f} {h.kda:<7.2f}")
    print("=" * 50)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dota Tracker - sync and analyze your Dota 2 stats")
    parser.add_argument("account_id", type=int, nargs="?", help="OpenDota/Steam32 account ID")
    parser.add_argument("-l", "--limit", type=int, default=50, help="Number of recent matches to sync (default: 50)")
    parser.add_argument("-o", "--output", type=Path, default=Path("output"), help="Output directory for charts")
    parser.add_argument("--no-sync", action="store_true", help="Only show stats from DB, skip syncing from OpenDota")
    args = parser.parse_args(argv)

    if args.account_id is None:
        parser.print_help()
        print("\nError: account_id required. Find it from your OpenDota/Steam profile URL.")
        return 1

    try:
        settings, session, client, use_case, player_repo, pm_repo, hero_repo = build_dependencies()

        account_id = AccountId(args.account_id)
        summary_obj = None

        if not args.no_sync:
            logger.info("Syncing player {id} (limit={limit})...", id=account_id, limit=args.limit)
            result = use_case.execute(account_id, limit=args.limit)
            logger.info(
                "Synced: players={p} matches={m} player_matches={pm}",
                p=result.players_synced,
                m=result.matches_synced,
                pm=result.player_matches_synced,
            )
        else:
            logger.info("Skipping sync, loading from database...")

        player = player_repo.get_by_account_id(account_id)
        if player is None:
            logger.error("Player {id} not found in DB. Run without --no-sync to fetch from OpenDota.", id=account_id)
            return 1

        from dota_tracker.infrastructure import models as orm
        from sqlalchemy import select
        pm_models = session.execute(
            select(orm.PlayerMatch).where(orm.PlayerMatch.player_id == player.id)
        ).scalars().all() if player.id is not None else []
        if not pm_models and player.id is not None:
            # fallback by account_id
            pm_models = session.execute(
                select(orm.PlayerMatch).where(orm.PlayerMatch.account_id == int(account_id))
            ).scalars().all()

        from dota_tracker.infrastructure.repositories import _player_match_to_domain, _hero_to_domain
        hero_models = session.execute(select(orm.Hero)).scalars().all()
        hero_by_internal_id = {h.id: _hero_to_domain(h) for h in hero_models}
        hero_by_external_id = {h.hero_id: hero_by_internal_id[h.id] for h in hero_models}

        player_matches = [_player_match_to_domain(pm) for pm in pm_models]
        # normalize hero ids for stats: PlayerMatch.hero_id stores internal hero id (FK)
        # StatsCalculator groups by hero_id; provide mapping keyed by internal hero id
        calc = StatsCalculator()
        summary = calc.compute(player, player_matches, hero_by_internal_id)
        print_summary(summary)

        charts = StatsCharts(output_dir=args.output)
        paths = charts.generate_all(summary, prefix=f"dota_{account_id}")
        print("\nCharts generated:")
        for p in paths:
            print(f"  - {p}")

        client.close()
        session.close()
        return 0
    except Exception as e:
        logger.error("Error: {err}", err=e)
        return 1


if __name__ == "__main__":
    sys.exit(main())