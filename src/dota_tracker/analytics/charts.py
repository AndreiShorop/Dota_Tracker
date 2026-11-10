"""Matplotlib chart generation for player stats."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dota_tracker.analytics.stats import PlayerSummary


class StatsCharts:
    def __init__(self, output_dir: Path | str = "output") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(self, summary: PlayerSummary, prefix: str = "stats") -> list[Path]:
        paths: list[Path] = []
        paths.append(self.winrate_pie(summary, prefix))
        if summary.top_heroes:
            paths.append(self.top_heroes_bar(summary, prefix))
            paths.append(self.top_heroes_kda(summary, prefix))
        return paths

    def winrate_pie(self, summary: PlayerSummary, prefix: str) -> Path:
        fig, ax = plt.subplots(figsize=(6, 6))
        if summary.total_games == 0 or (summary.wins == 0 and summary.losses == 0):
            ax.text(0.5, 0.5, "No win/loss data", ha="center", va="center")
            ax.axis("off")
            ax.set_title(f"{summary.player.persona_name or 'Player'} - Winrate")
        else:
            labels = []
            sizes = []
            colors = []
            if summary.wins > 0:
                labels.append("Wins")
                sizes.append(summary.wins)
                colors.append("#2ecc71")
            if summary.losses > 0:
                labels.append("Losses")
                sizes.append(summary.losses)
                colors.append("#e74c3c")
            if sizes:
                ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%", startangle=90)
            ax.set_title(f"{summary.player.persona_name or 'Player'} - Winrate")
        path = self.output_dir / f"{prefix}_winrate.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def top_heroes_bar(self, summary: PlayerSummary, prefix: str) -> Path:
        heroes = summary.top_heroes[:10]
        fig, ax = plt.subplots(figsize=(10, 6))
        names = [h.hero_name for h in heroes]
        wins = [h.wins for h in heroes]
        losses = [h.losses for h in heroes]
        ax.bar(names, wins, label="Wins", color="#2ecc71")
        ax.bar(names, losses, bottom=wins, label="Losses", color="#e74c3c")
        ax.set_title("Top Heroes - Record")
        ax.set_ylabel("Games")
        ax.legend()
        plt.xticks(rotation=45, ha="right")
        path = self.output_dir / f"{prefix}_heroes_record.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path

    def top_heroes_kda(self, summary: PlayerSummary, prefix: str) -> Path:
        heroes = summary.top_heroes[:10]
        fig, ax = plt.subplots(figsize=(10, 6))
        names = [h.hero_name for h in heroes]
        kdas = [h.kda for h in heroes]
        ax.bar(names, kdas, color="#3498db")
        ax.set_title("Top Heroes - KDA")
        ax.set_ylabel("KDA (K+A)/D")
        plt.xticks(rotation=45, ha="right")
        path = self.output_dir / f"{prefix}_heroes_kda.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        return path