"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-10 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("steam_id", sa.Text(), nullable=True),
        sa.Column("persona_name", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("profile_url", sa.Text(), nullable=True),
        sa.Column("country_code", sa.Text(), nullable=True),
        sa.Column("last_match_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_tracked", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("account_id", name="uq_players_account_id"),
    )
    op.create_index("ix_players_persona_name", "players", ["persona_name"])
    op.create_index("ix_players_is_tracked", "players", ["is_tracked"])

    op.create_table(
        "heroes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("hero_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("localized_name", sa.Text(), nullable=False),
        sa.Column("primary_attr", sa.Text(), nullable=True),
        sa.Column("attack_type", sa.Text(), nullable=True),
        sa.Column("roles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("legs", sa.SmallInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("hero_id", name="uq_heroes_hero_id"),
        sa.UniqueConstraint("name", name="uq_heroes_name"),
    )
    op.create_index("ix_heroes_localized_name", "heroes", ["localized_name"])

    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("localized_name", sa.Text(), nullable=True),
        sa.Column("cost", sa.Integer(), nullable=True),
        sa.Column("is_recipe", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("in_secret_shop", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("in_side_shop", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("item_id", name="uq_items_item_id"),
    )
    op.create_index("ix_items_name", "items", ["name"])
    op.create_index("ix_items_localized_name", "items", ["localized_name"])

    op.create_table(
        "matches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.BigInteger(), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("game_mode", sa.Integer(), nullable=True),
        sa.Column("lobby_type", sa.Integer(), nullable=True),
        sa.Column("radiant_win", sa.Boolean(), nullable=True),
        sa.Column("radiant_score", sa.Integer(), nullable=True),
        sa.Column("dire_score", sa.Integer(), nullable=True),
        sa.Column("patch", sa.Integer(), nullable=True),
        sa.Column("region", sa.Integer(), nullable=True),
        sa.Column("radiant_team_id", sa.BigInteger(), nullable=True),
        sa.Column("dire_team_id", sa.BigInteger(), nullable=True),
        sa.Column("raw_match", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", name="uq_matches_match_id"),
    )
    op.create_index("ix_matches_start_time", "matches", ["start_time"])
    op.create_index("ix_matches_game_mode", "matches", ["game_mode"])
    op.create_index("ix_matches_patch", "matches", ["patch"])

    op.create_table(
        "player_matches",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("match_id", sa.BigInteger(), nullable=False),
        sa.Column("player_id", sa.BigInteger(), nullable=True),
        sa.Column("account_id", sa.BigInteger(), nullable=True),
        sa.Column("hero_id", sa.Integer(), nullable=False),
        sa.Column("player_slot", sa.Integer(), nullable=False),
        sa.Column("is_radiant", sa.Boolean(), nullable=False),
        sa.Column("win", sa.Boolean(), nullable=True),
        sa.Column("kills", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("deaths", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("assists", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("gold_per_min", sa.Integer(), nullable=True),
        sa.Column("xp_per_min", sa.Integer(), nullable=True),
        sa.Column("last_hits", sa.Integer(), nullable=True),
        sa.Column("denies", sa.Integer(), nullable=True),
        sa.Column("hero_damage", sa.Integer(), nullable=True),
        sa.Column("tower_damage", sa.Integer(), nullable=True),
        sa.Column("hero_healing", sa.Integer(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("item_0_id", sa.Integer(), nullable=True),
        sa.Column("item_1_id", sa.Integer(), nullable=True),
        sa.Column("item_2_id", sa.Integer(), nullable=True),
        sa.Column("item_3_id", sa.Integer(), nullable=True),
        sa.Column("item_4_id", sa.Integer(), nullable=True),
        sa.Column("item_5_id", sa.Integer(), nullable=True),
        sa.Column("item_neutral_id", sa.Integer(), nullable=True),
        sa.Column("lane", sa.Integer(), nullable=True),
        sa.Column("role", sa.Integer(), nullable=True),
        sa.Column("raw_player", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["hero_id"], ["heroes.id"], name="fk_player_matches_hero_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["match_id"], ["matches.id"], name="fk_player_matches_match_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"], name="fk_player_matches_player_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["item_0_id"], ["items.id"], name="fk_player_matches_item_0_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["item_1_id"], ["items.id"], name="fk_player_matches_item_1_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["item_2_id"], ["items.id"], name="fk_player_matches_item_2_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["item_3_id"], ["items.id"], name="fk_player_matches_item_3_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["item_4_id"], ["items.id"], name="fk_player_matches_item_4_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["item_5_id"], ["items.id"], name="fk_player_matches_item_5_id", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["item_neutral_id"], ["items.id"], name="fk_player_matches_item_neutral_id", ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("match_id", "player_slot", name="uq_player_matches_match_player_slot"),
        sa.CheckConstraint("kills >= 0", name="ck_player_matches_kills_non_negative"),
        sa.CheckConstraint("deaths >= 0", name="ck_player_matches_deaths_non_negative"),
        sa.CheckConstraint("assists >= 0", name="ck_player_matches_assists_non_negative"),
        sa.CheckConstraint("player_slot >= 0 AND player_slot <= 255", name="ck_player_matches_player_slot_range"),
    )
    op.create_index("ix_player_matches_match_id", "player_matches", ["match_id"])
    op.create_index("ix_player_matches_player_id", "player_matches", ["player_id"])
    op.create_index("ix_player_matches_account_id", "player_matches", ["account_id"], postgresql_where=sa.text("account_id IS NOT NULL"))
    op.create_index("ix_player_matches_hero_id", "player_matches", ["hero_id"])
    op.create_index("ix_player_matches_match_id_is_radiant", "player_matches", ["match_id", "is_radiant"])


def downgrade() -> None:
    op.drop_table("player_matches")
    op.drop_table("matches")
    op.drop_table("items")
    op.drop_table("heroes")
    op.drop_table("players")
