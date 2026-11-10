# Database Schema

## Overview

Dota Tracker uses PostgreSQL as its primary relational datastore. The schema is designed to store core Dota 2 entities (players, heroes, items, matches) and the per-player participation details for each match. SQLAlchemy 2.x models and Alembic migrations should implement and evolve this schema.

Conventions:
- Primary keys are surrogate integer/bigint identifiers where appropriate, with natural/external IDs stored as unique indexed columns (e.g., OpenDota/Steam IDs).
- Timestamps are stored as `TIMESTAMP WITH TIME ZONE` (`timestamptz`).
- JSON-capable fields may use `JSONB` for extensible raw payload fragments when needed.
- Foreign keys enforce referential integrity; indexes support common lookup and join paths.

## Tables

### `players`

Represents a Dota 2 player/account tracked by the application.

| Column | Type | Nullable | Default | Constraints / Notes |
| --- | --- | --- | --- | --- |
| `id` | `BIGSERIAL` | No | identity | **Primary key** |
| `account_id` | `BIGINT` | No | - | **Unique**. OpenDota/Steam32 account identifier |
| `steam_id` | `VARCHAR(32)` | Yes | `NULL` | Optional SteamID representation |
| `persona_name` | `VARCHAR(255)` | Yes | `NULL` | Last known display name |
| `avatar_url` | `TEXT` | Yes | `NULL` | Profile avatar URL |
| `profile_url` | `TEXT` | Yes | `NULL` | Profile page URL |
| `country_code` | `VARCHAR(8)` | Yes | `NULL` | Optional country/region code |
| `last_match_time` | `TIMESTAMPTZ` | Yes | `NULL` | Last known match timestamp |
| `is_tracked` | `BOOLEAN` | No | `FALSE` | Whether app actively syncs this player |
| `raw_profile` | `JSONB` | Yes | `NULL` | Optional raw API payload snapshot |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Record creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last update time |

**Indexes:**
- `pk_players` on (`id`) — primary key
- `uq_players_account_id` on (`account_id`) — unique
- `ix_players_persona_name` on (`persona_name`) — name lookup/search support
- `ix_players_is_tracked` on (`is_tracked`) — tracked player queries

### `heroes`

Canonical Dota 2 hero catalog.

| Column | Type | Nullable | Default | Constraints / Notes |
| --- | --- | --- | --- | --- |
| `id` | `SERIAL` | No | identity | **Primary key** (internal) |
| `hero_id` | `INTEGER` | No | - | **Unique**. OpenDota/Dota hero ID |
| `name` | `VARCHAR(128)` | No | - | Internal/registry name (e.g., `npc_dota_hero_axe`) |
| `localized_name` | `VARCHAR(128)` | No | - | Display name |
| `primary_attr` | `VARCHAR(16)` | Yes | `NULL` | `str`, `agi`, `int`, `all`, or provider value |
| `attack_type` | `VARCHAR(16)` | Yes | `NULL` | Melee/Ranged |
| `roles` | `JSONB` | Yes | `NULL` | Array/list of roles |
| `legs` | `SMALLINT` | Yes | `NULL` | Cosmetic/stat metadata if provided |
| `is_active` | `BOOLEAN` | No | `TRUE` | Availability flag |
| `raw_data` | `JSONB` | Yes | `NULL` | Optional raw API payload |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Record creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last update time |

**Indexes:**
- `pk_heroes` on (`id`) — primary key
- `uq_heroes_hero_id` on (`hero_id`) — unique
- `uq_heroes_name` on (`name`) — unique
- `ix_heroes_localized_name` on (`localized_name`) — lookup/display

### `items`

Canonical Dota 2 item catalog.

| Column | Type | Nullable | Default | Constraints / Notes |
| --- | --- | --- | --- | --- |
| `id` | `SERIAL` | No | identity | **Primary key** (internal) |
| `item_id` | `INTEGER` | No | - | **Unique**. OpenDota/Dota item ID |
| `name` | `VARCHAR(128)` | Yes | `NULL` | Internal/registry name (nullable if unknown) |
| `localized_name` | `VARCHAR(128)` | Yes | `NULL` | Display name |
| `cost` | `INTEGER` | Yes | `NULL` | Gold cost |
| `is_recipe` | `BOOLEAN` | No | `FALSE` | Recipe flag |
| `in_secret_shop` | `BOOLEAN` | No | `FALSE` | Secret shop availability |
| `in_side_shop` | `BOOLEAN` | No | `FALSE` | Side shop availability (legacy/data-dependent) |
| `raw_data` | `JSONB` | Yes | `NULL` | Optional raw API payload |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Record creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last update time |

**Indexes:**
- `pk_items` on (`id`) — primary key
- `uq_items_item_id` on (`item_id`) — unique
- `ix_items_name` on (`name`) — lookup
- `ix_items_localized_name` on (`localized_name`) — lookup/display

### `matches`

Represents a single Dota 2 match.

| Column | Type | Nullable | Default | Constraints / Notes |
| --- | --- | --- | --- | --- |
| `id` | `BIGSERIAL` | No | identity | **Primary key** (internal) |
| `match_id` | `BIGINT` | No | - | **Unique**. OpenDota/Dota match ID |
| `start_time` | `TIMESTAMPTZ` | Yes | `NULL` | Match start time |
| `duration_seconds` | `INTEGER` | Yes | `NULL` | Match duration in seconds |
| `game_mode` | `INTEGER` | Yes | `NULL` | Game mode code |
| `lobby_type` | `INTEGER` | Yes | `NULL` | Lobby type code |
| `radiant_win` | `BOOLEAN` | Yes | `NULL` | Winner flag |
| `radiant_score` | `INTEGER` | Yes | `NULL` | Radiant kills/score |
| `dire_score` | `INTEGER` | Yes | `NULL` | Dire kills/score |
| `patch` | `INTEGER` | Yes | `NULL` | Patch identifier if available |
| `region` | `INTEGER` | Yes | `NULL` | Region/cluster identifier |
| `radiant_team_id` | `BIGINT` | Yes | `NULL` | Optional team ID |
| `dire_team_id` | `BIGINT` | Yes | `NULL` | Optional team ID |
| `raw_match` | `JSONB` | Yes | `NULL` | Optional raw API payload snapshot |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Record creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last update time |

**Indexes:**
- `pk_matches` on (`id`) — primary key
- `uq_matches_match_id` on (`match_id`) — unique
- `ix_matches_start_time` on (`start_time`) — time-range queries
- `ix_matches_game_mode` on (`game_mode`) — filtering
- `ix_matches_patch` on (`patch`) — patch-based analysis

### `player_matches`

Association table storing per-player performance and state for a match (fact table).

| Column | Type | Nullable | Default | Constraints / Notes |
| --- | --- | --- | --- | --- |
| `id` | `BIGSERIAL` | No | identity | **Primary key** (surrogate) |
| `match_id` | `BIGINT` | No | - | **FK** → `matches.id` (`ON DELETE CASCADE`) |
| `player_id` | `BIGINT` | Yes | `NULL` | **FK** → `players.id` (`ON DELETE SET NULL`), nullable for anonymous players |
| `account_id` | `BIGINT` | Yes | `NULL` | OpenDota account ID snapshot (for anonymous/untracked resolution) |
| `hero_id` | `INTEGER` | No | - | **FK** → `heroes.id` (`ON DELETE RESTRICT`) |
| `player_slot` | `INTEGER` | No | - | Dota player slot (encodes team/position) |
| `is_radiant` | `BOOLEAN` | No | - | Team flag derived/stored for query efficiency |
| `win` | `BOOLEAN` | Yes | `NULL` | Player win flag |
| `kills` | `INTEGER` | No | `0` | Kills |
| `deaths` | `INTEGER` | No | `0` | Deaths |
| `assists` | `INTEGER` | No | `0` | Assists |
| `gold_per_min` | `INTEGER` | Yes | `NULL` | GPM |
| `xp_per_min` | `INTEGER` | Yes | `NULL` | XPM |
| `last_hits` | `INTEGER` | Yes | `NULL` | Last hits |
| `denies` | `INTEGER` | Yes | `NULL` | Denies |
| `hero_damage` | `INTEGER` | Yes | `NULL` | Hero damage |
| `tower_damage` | `INTEGER` | Yes | `NULL` | Tower damage |
| `hero_healing` | `INTEGER` | Yes | `NULL` | Hero healing |
| `level` | `INTEGER` | Yes | `NULL` | Hero level at end |
| `item_0_id` | `INTEGER` | Yes | `NULL` | **FK** → `items.id` (`ON DELETE SET NULL`) |
| `item_1_id` | `INTEGER` | Yes | `NULL` | **FK** → `items.id` (`ON DELETE SET NULL`) |
| `item_2_id` | `INTEGER` | Yes | `NULL` | **FK** → `items.id` (`ON DELETE SET NULL`) |
| `item_3_id` | `INTEGER` | Yes | `NULL` | **FK** → `items.id` (`ON DELETE SET NULL`) |
| `item_4_id` | `INTEGER` | Yes | `NULL` | **FK** → `items.id` (`ON DELETE SET NULL`) |
| `item_5_id` | `INTEGER` | Yes | `NULL` | **FK** → `items.id` (`ON DELETE SET NULL`) |
| `item_neutral_id` | `INTEGER` | Yes | `NULL` | **FK** → `items.id` (`ON DELETE SET NULL`) |
| `lane` | `INTEGER` | Yes | `NULL` | Lane/role code if available |
| `role` | `INTEGER` | Yes | `NULL` | Parsed role if available |
| `raw_player` | `JSONB` | Yes | `NULL` | Optional raw player payload snapshot |
| `created_at` | `TIMESTAMPTZ` | No | `now()` | Record creation time |
| `updated_at` | `TIMESTAMPTZ` | No | `now()` | Last update time |

**Constraints:**
- `uq_player_matches_match_player_slot` unique on (`match_id`, `player_slot`) — one record per slot per match
- `uq_player_matches_match_account` unique on (`match_id`, `account_id`) where `account_id IS NOT NULL` (recommended partial index) — prevents duplicate tracked player rows
- Check constraints (recommended): non-negative stats, valid `player_slot` range

**Indexes:**
- `pk_player_matches` on (`id`) — primary key
- `ix_player_matches_match_id` on (`match_id`) — join/filter by match
- `ix_player_matches_player_id` on (`player_id`) — player history queries
- `ix_player_matches_account_id` on (`account_id`) — lookup by external account
- `ix_player_matches_hero_id` on (`hero_id`) — hero-based analytics
- `ix_player_matches_match_id_is_radiant` on (`match_id`, `is_radiant`) — team splits

## Relationships

- **players 1 — N player_matches**: A tracked player can appear in many matches (`player_matches.player_id` → `players.id`, nullable for anonymous/unresolved).
- **matches 1 — N player_matches**: A match contains multiple player participation records (`player_matches.match_id` → `matches.id`).
- **heroes 1 — N player_matches**: Each player-match record references one hero (`player_matches.hero_id` → `heroes.id`).
- **items 1 — N player_matches (optional, multiple slots)**: Each item slot in `player_matches` may reference an item (`item_*_id` → `items.id`).

Cardinality notes:
- A standard Dota 2 match yields up to 10 `player_matches` rows.
- Not all players in a match are necessarily tracked/stored in `players`; `account_id` may be null for anonymous players.

## ASCII ER Diagram

```text
+-------------------+            +----------------------+
|      players      |            |        heroes        |
+-------------------+            +----------------------+
| PK id             |            | PK id                |
| UQ account_id     |            | UQ hero_id           |
|    persona_name   |            | UQ name              |
|    steam_id       |            |    localized_name    |
|    is_tracked     |            |    primary_attr      |
|    ...            |            |    roles (JSONB)     |
+---------+---------+            +----------+-----------+
          | 1                               | 1
          |                                 |
          | N                               | N
          |                                 |
          |      +-------------------+      |
          +----->|   player_matches  |<-----+
                 +-------------------+
                 | PK id             |
                 | FK match_id   ----+----+
                 | FK player_id      |    |
                 |    account_id     |    |
                 | FK hero_id        |    |
                 |    player_slot    |    |
                 |    is_radiant     |    |
                 |    kills/deaths/  |    |
                 |    assists/...    |    |
                 | FK item_0_id  ------+  |
                 | FK item_1_id  ------+  |
                 | FK item_2_id  ------+  |        +-------------------+
                 | FK item_3_id  ------+--------->|       items       |
                 | FK item_4_id  ------+  |        +-------------------+
                 | FK item_5_id  ------+  |        | PK id             |
                 | FK item_neutral_id--+  |        | UQ item_id        |
                 +----------+--------+    |        |    name           |
                            | N           |        |    localized_name |
                            |             |        |    cost           |
                            | 1           |        +-------------------+
                 +----------v--------+
                 |      matches      |
                 +-------------------+
                 | PK id             |
                 | UQ match_id       |
                 |    start_time     |
                 |    duration_sec   |
                 |    radiant_win    |
                 |    game_mode      |
                 |    patch/region   |
                 |    ...            |
                 +-------------------+
```

## Migration and Evolution Notes

- Use Alembic migrations for all schema changes; avoid manual drift in production databases.
- Add/adjust indexes based on observed query patterns (player history, match lookup, hero/item analytics).
- Consider partitioning `matches`/`player_matches` by time at scale (future).
- Store raw API payloads (`JSONB`) selectively for traceability/debugging; avoid duplicating normalized fields unnecessarily.
