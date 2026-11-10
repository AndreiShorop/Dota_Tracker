"""SQLAlchemy read adapter for stored dashboard projections."""

from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from dota_tracker.application.dtos import DashboardMatch, DashboardPlayer, PlayerDashboard
from dota_tracker.infrastructure.models import Hero, Match, Player, PlayerMatch
from dota_tracker.shared.types import AccountId


def hero_image_url(name: str | None) -> str | None:
    """Return a CDN URL only for a valid OpenDota hero registry name."""
    if name is None or re.fullmatch(r"npc_dota_hero_[a-z0-9_]+", name) is None:
        return None
    slug = name.removeprefix("npc_dota_hero_")
    return f"https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/{slug}.png"


def project_player(player: Player) -> DashboardPlayer:
    """Project a stored player without exposing its private profile payload."""
    return DashboardPlayer(
        account_id=player.account_id,
        persona_name=player.persona_name,
        avatar_url=player.avatar_url,
    )


def project_match(match: Match, participation: PlayerMatch, hero: Hero) -> DashboardMatch:
    """Project joined ORM rows using external match and hero identifiers."""
    return DashboardMatch(
        match_id=match.match_id,
        start_time=match.start_time,
        duration_seconds=match.duration_seconds,
        hero_id=hero.hero_id,
        hero_name=hero.localized_name,
        hero_image=hero_image_url(hero.name),
        win=participation.win,
        kills=participation.kills,
        deaths=participation.deaths,
        assists=participation.assists,
        gold_per_min=participation.gold_per_min,
        xp_per_min=participation.xp_per_min,
        last_hits=participation.last_hits,
        hero_damage=participation.hero_damage,
        tower_damage=participation.tower_damage,
        hero_healing=participation.hero_healing,
        is_radiant=participation.is_radiant,
        game_mode=match.game_mode,
    )


class SqlAlchemyDashboardReader:
    """Read all stored players and their stored match histories."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_players(self) -> list[DashboardPlayer]:
        """Return profiles sorted by account ID, including untracked players."""
        players = self._session.scalars(select(Player).order_by(Player.account_id)).all()
        return [project_player(player) for player in players]

    def get_dashboard(self, account_id: AccountId) -> PlayerDashboard | None:
        """Join participation via internal keys and return newest stored matches first."""
        player = self._session.scalar(select(Player).where(Player.account_id == account_id))
        if player is None:
            return None
        rows = self._session.execute(
            select(Match, PlayerMatch, Hero)
            .join(PlayerMatch, PlayerMatch.match_id == Match.id)
            .join(Hero, Hero.id == PlayerMatch.hero_id)
            .where(
                or_(
                    PlayerMatch.player_id == player.id,
                    (PlayerMatch.player_id.is_(None)) & (PlayerMatch.account_id == account_id),
                )
            )
            .order_by(Match.start_time.desc().nulls_last(), Match.match_id.desc())
        ).all()
        return PlayerDashboard(
            player=project_player(player),
            matches=[
                project_match(match, participation, hero) for match, participation, hero in rows
            ],
        )
