"""SQLAlchemy ORM models for the Dota Tracker schema.

Tables: players, matches, heroes, items, player_matches. Raw API payloads are
stored selectively in JSONB columns for traceability. Column names and
constraints mirror docs/database_schema.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dota_tracker.infrastructure.database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    steam_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    persona_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    country_code: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_match_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_tracked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_profile: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    player_matches: Mapped[list[PlayerMatch]] = relationship(
        back_populates="player", foreign_keys="PlayerMatch.player_id"
    )

    __table_args__ = (
        UniqueConstraint("account_id", name="uq_players_account_id"),
        Index("ix_players_persona_name", "persona_name"),
        Index("ix_players_is_tracked", "is_tracked"),
    )


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    game_mode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    lobby_type: Mapped[int | None] = mapped_column(Integer, nullable=True)
    radiant_win: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    radiant_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dire_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    patch: Mapped[int | None] = mapped_column(Integer, nullable=True)
    region: Mapped[int | None] = mapped_column(Integer, nullable=True)
    radiant_team_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    dire_team_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    raw_match: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    player_matches: Mapped[list[PlayerMatch]] = relationship(
        back_populates="match", foreign_keys="PlayerMatch.match_id"
    )

    __table_args__ = (
        UniqueConstraint("match_id", name="uq_matches_match_id"),
        Index("ix_matches_start_time", "start_time"),
        Index("ix_matches_game_mode", "game_mode"),
        Index("ix_matches_patch", "patch"),
    )


class Hero(Base):
    __tablename__ = "heroes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    localized_name: Mapped[str] = mapped_column(Text, nullable=False)
    primary_attr: Mapped[str | None] = mapped_column(Text, nullable=True)
    attack_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    roles: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    legs: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    player_matches: Mapped[list[PlayerMatch]] = relationship(
        back_populates="hero", foreign_keys="PlayerMatch.hero_id"
    )

    __table_args__ = (Index("ix_heroes_localized_name", "localized_name"),)


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, unique=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    localized_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_recipe: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    in_secret_shop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    in_side_shop: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        Index("ix_items_name", "name"),
        Index("ix_items_localized_name", "localized_name"),
    )


class PlayerMatch(Base):
    __tablename__ = "player_matches"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    account_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    hero_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("heroes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    player_slot: Mapped[int] = mapped_column(Integer, nullable=False)
    is_radiant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    win: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    kills: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    deaths: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assists: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gold_per_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    xp_per_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_hits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    denies: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hero_damage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tower_damage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hero_healing: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    item_0_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    item_1_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    item_2_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    item_3_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    item_4_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    item_5_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    item_neutral_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("items.id", ondelete="SET NULL"), nullable=True
    )
    lane: Mapped[int | None] = mapped_column(Integer, nullable=True)
    role: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_player: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    player: Mapped[Player | None] = relationship(back_populates="player_matches")
    match: Mapped[Match] = relationship(back_populates="player_matches")
    hero: Mapped[Hero] = relationship(back_populates="player_matches")

    __table_args__ = (
        UniqueConstraint("match_id", "player_slot", name="uq_player_matches_match_player_slot"),
        Index(
            "ix_player_matches_account_id",
            "account_id",
            postgresql_where=text("account_id IS NOT NULL"),
        ),
        Index("ix_player_matches_player_id", "player_id"),
        Index("ix_player_matches_hero_id", "hero_id"),
        Index("ix_player_matches_match_id_is_radiant", "match_id", "is_radiant"),
        CheckConstraint("kills >= 0", name="ck_player_matches_kills_non_negative"),
        CheckConstraint("deaths >= 0", name="ck_player_matches_deaths_non_negative"),
        CheckConstraint("assists >= 0", name="ck_player_matches_assists_non_negative"),
        CheckConstraint(
            "player_slot >= 0 AND player_slot <= 255",
            name="ck_player_matches_player_slot_range",
        ),
    )


__all__ = [
    "Base",
    "Hero",
    "Item",
    "Match",
    "Player",
    "PlayerMatch",
]
