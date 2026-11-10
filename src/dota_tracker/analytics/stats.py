"""Player statistics aggregation from stored match data."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Sequence

from dota_tracker.domain.entities import Hero, Match, Player, PlayerMatch


@dataclass(frozen=True)
class HeroStat:
    hero_id: int
    hero_name: str
    games: int
    wins: int
    losses: int
    winrate: float
    kills: float
    deaths: float
    assists: float
    kda: float


@dataclass(frozen=True)
class PlayerSummary:
    player: Player
    total_games: int
    wins: int
    losses: int
    winrate: float
    avg_kills: float
    avg_deaths: float
    avg_assists: float
    avg_kda: float
    top_heroes: list[HeroStat]


class StatsCalculator:
    def compute(
        self,
        player: Player,
        player_matches: Sequence[PlayerMatch],
        heroes: dict[int, Hero],
        matches: dict[int, Match] | None = None,
    ) -> PlayerSummary:
        if not player_matches:
            return PlayerSummary(
                player=player,
                total_games=0,
                wins=0,
                losses=0,
                winrate=0.0,
                avg_kills=0.0,
                avg_deaths=0.0,
                avg_assists=0.0,
                avg_kda=0.0,
                top_heroes=[],
            )

        total_games = len(player_matches)
        wins = sum(1 for pm in player_matches if pm.win is True)
        losses = sum(1 for pm in player_matches if pm.win is False)
        winrate = (wins / total_games * 100.0) if total_games > 0 else 0.0

        total_kills = sum(pm.kills for pm in player_matches)
        total_deaths = sum(pm.deaths for pm in player_matches)
        total_assists = sum(pm.assists for pm in player_matches)
        avg_kills = total_kills / total_games
        avg_deaths = total_deaths / total_games
        avg_assists = total_assists / total_games
        avg_kda = (total_kills + total_assists) / max(total_deaths, 1)

        hero_agg: dict[int, dict[str, float]] = defaultdict(
            lambda: {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0}
        )
        for pm in player_matches:
            h = hero_agg[pm.hero_id]
            h["games"] += 1
            if pm.win is True:
                h["wins"] += 1
            h["kills"] += pm.kills
            h["deaths"] += pm.deaths
            h["assists"] += pm.assists

        top_heroes: list[HeroStat] = []
        for hero_id, agg in hero_agg.items():
            games = int(agg["games"])
            hero_wins = int(agg["wins"])
            hero_losses = games - hero_wins
            hero_wr = (hero_wins / games * 100.0) if games > 0 else 0.0
            hk = agg["kills"] / games
            hd = agg["deaths"] / games
            ha = agg["assists"] / games
            hkda = (agg["kills"] + agg["assists"]) / max(agg["deaths"], 1.0)
            hero = heroes.get(hero_id)
            hero_name = hero.localized_name if hero and hero.localized_name else f"Hero {hero_id}"
            top_heroes.append(
                HeroStat(
                    hero_id=hero_id,
                    hero_name=hero_name,
                    games=games,
                    wins=hero_wins,
                    losses=hero_losses,
                    winrate=hero_wr,
                    kills=hk,
                    deaths=hd,
                    assists=ha,
                    kda=hkda,
                )
            )
        top_heroes.sort(key=lambda x: (x.games, x.winrate), reverse=True)

        return PlayerSummary(
            player=player,
            total_games=total_games,
            wins=wins,
            losses=losses,
            winrate=winrate,
            avg_kills=avg_kills,
            avg_deaths=avg_deaths,
            avg_assists=avg_assists,
            avg_kda=avg_kda,
            top_heroes=top_heroes,
        )