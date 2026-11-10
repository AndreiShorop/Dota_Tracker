# Dota Tracker

Dota Tracker provides local Dota 2 analytics through a web dashboard and a CLI, backed by PostgreSQL and OpenDota.

## Features

- **Local web dashboard**: Interactive player and match analysis served by FastAPI.
- **Match and player analysis**: Store and analyze players, matches, heroes, items, and per-player match performance.
- **OpenDota integration**: Designed for structured ingestion from the OpenDota API with validation, retry handling, and rate limiting.
- **Relational persistence**: PostgreSQL schema managed through SQLAlchemy and Alembic for durable, queryable analytics data.
- **Analytics-ready data model**: Tabular analysis with pandas/numpy and visualization support with matplotlib.
- **Clean architecture**: Clear separation between domain, application, infrastructure, and presentation concerns for maintainability and testability.
- **Typed and testable codebase**: Python 3.13, Pydantic models, strict mypy configuration, pytest, and ruff for consistent quality.

## Technology Stack

| Area | Technology |
| --- | --- |
| Language | Python 3.13 |
| Desktop UI | PySide6 (Qt for Python) |
| Web server | FastAPI, Uvicorn |
| Database | PostgreSQL 16 |
| ORM / Migrations | SQLAlchemy 2.x, Alembic |
| Data Validation / Settings | Pydantic v2, pydantic-settings |
| API Client | httpx |
| Analytics / Visualization | pandas, numpy, matplotlib |
| Logging | loguru |
| Configuration | `.env` + PyYAML |
| Testing | pytest, pytest-asyncio, pytest-cov |
| Quality | ruff, mypy (strict) |
| Containerization | Docker, Docker Compose |

## Architecture Overview

Dota Tracker follows clean architecture with dependencies pointing inward:

- **Presentation layer (`src/dota_tracker/presentation`)**: PySide6 UI components, view models/controllers, and user interaction flows. Depends on application interfaces and DTOs.
- **Application layer (`src/dota_tracker/application`)**: Use cases, orchestration, command/query handlers, and port definitions (interfaces). Coordinates domain logic and infrastructure without knowing framework details.
- **Domain layer (`src/dota_tracker/domain`)**: Core entities, value objects, domain services, and business rules. Pure and framework-independent.
- **Infrastructure layer (`src/dota_tracker/infrastructure`)**: Adapters implementing ports: PostgreSQL repositories, OpenDota client, Alembic migrations, logging, and configuration providers.
- **Analytics layer (`src/dota_tracker/analytics`)**: Data transformation, aggregations, metrics computation, and plotting utilities that consume application/domain outputs.

**Dependency rule:** `presentation -> application -> domain`, and `infrastructure -> application/domain` via ports and adapters. Inner layers must not import from outer layers.

## Docker quick start (Windows PowerShell)

Install and start Docker Desktop with Compose, then run from the project directory:

```powershell
if (-not (Test-Path .env)) { Copy-Item example.env .env }
# Edit .env if needed; retain the credentials used by an existing database.
docker compose up -d --build
docker compose ps
docker compose logs -f web
```

Open http://127.0.0.1:8080 (API docs: http://127.0.0.1:8080/docs). The web service
waits for PostgreSQL to report healthy, runs Alembic migrations, and only then starts
the server. Initial startup and image building may take time; use Ctrl+C to leave logs.
OpenDota settings come from the same `.env` as the local application. Inside the web
container the database URL is built from `POSTGRES_USER`, `POSTGRES_PASSWORD`, and
`POSTGRES_DB` using the Compose database hostname, not the host `DATABASE_URL`.
For passwords containing `$` or `#`, use single quotes around the value in `.env`
so Compose does not interpolate it. Shell environment variables override `.env`
values in Compose; ensure any overrides match the existing database.

The existing `dota-postgres` container, host port 5433, and named volume
`dota_postgres_data` are retained, so existing local data remains in place. PostgreSQL
uses the `POSTGRES_*` initialization credentials only when creating a **new** volume:
editing `.env` does not change credentials or the database in an existing volume.
Use the existing values or change credentials in PostgreSQL separately before updating
configuration. Migrations update the existing schema, so back up important data first.

The website is published on loopback only and has no authentication: do not expose it
publicly. The existing PostgreSQL port mapping is unchanged and may listen on all host
interfaces; use a firewall if needed. If port 8080 or 5433 is occupied, stop the
conflicting service or adjust the corresponding host port mapping. A container-name
conflict can also occur if another project owns `dota-postgres`. For startup or
authentication errors, inspect `docker compose ps` and
`docker compose logs web dota-postgres`; verify the existing volume's credentials.
Stop services without deleting data using:

```powershell
docker compose stop
```

Do not use `docker compose down -v`: it removes the named database volume.

### Local Python / CLI alternative

Python 3.13 is required. With PostgreSQL running, configure `DATABASE_URL` in `.env`
for the host (normally port 5433); URL-encode special characters in its credentials.
The Docker web container ignores this host URL, but local commands use it.

```powershell
docker compose up -d dota-postgres
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e '.[dev]'
alembic upgrade head
python -m dota_tracker.presentation.web
```

The local Python web server uses http://127.0.0.1:8000. To populate a player, use its
dashboard sync action or `python -m dota_tracker 1275812207 --limit 50`; the CLI also
supports `--no-sync` for stored data.

The dashboard uses stored matches; a recent sync does not automatically include older
history. Use `python -m dota_tracker 1275812207 --all-matches` or call
`POST /api/players/{account_id}/sync?all_matches=true` to request all matches OpenDota
currently makes available. The default endpoint syncs 50; `?limit=N` accepts 1 through
2147483647 and is not capped at 100. If both options are supplied, `all_matches=true`
takes precedence. The response counts processed player, match, and participation rows,
including updates, not just newly inserted rows.

History uses OpenDota's player matches endpoint with `significant=0` and 100-row pages.
It is limited by the provider's data, privacy, availability, and possible changes during
pagination; it is not proof of a player's complete lifetime history. Matches without
usable player/hero information may not have a participation row. The request runs
synchronously and can take a long time: clients should show a pending state and allow
for timeouts. A client timeout or disconnect does not necessarily cancel the server-side
sync; check stored results before retrying. Per-page calls use the configured rate limit and bounded retries, including
429 responses. Large histories use many database operations and one potentially long
transaction. A failed sync rolls back its changes; existing stored history is not deleted.
Retry the sync after errors or provider data changes. Offset paging cannot guarantee a
snapshot if OpenDota changes history during the request; anomalies may fail the sync,
and a later sync may be needed to pick up concurrent changes.

Missing fields and the unavailable sync timestamp are `null`; a player with no stored
matches has an empty match list. `GET /api/matches/{match_id}` fetches match details and
participant items directly from OpenDota, independently of stored dashboard data;
availability depends on the provider. Other endpoints include `GET /api/players` and
`GET /api/players/{account_id}/dashboard`.

## Project Structure

```text
Dota_Tracker/
├─ example.env
├─ .gitignore
├─ AGENTS.md
├─ Dockerfile
├─ docker-compose.yml
├─ pyproject.toml
├─ README.md
├─ docs/
│  ├─ api_integration.md
│  ├─ architecture.md
│  └─ database_schema.md
└─ src/
   └─ dota_tracker/                # Application package (to be implemented)
      ├─ __init__.py
      ├─ __main__.py               # CLI/desktop entry point
      ├─ domain/                   # Entities, value objects, domain services
      ├─ application/              # Use cases, ports (interfaces), DTOs
      ├─ infrastructure/           # DB, API clients, adapters, migrations
      ├─ presentation/             # PySide6 UI, views, controllers/viewmodels
      └─ analytics/                # Metrics, aggregations, visualizations
```

Additional directories may include `tests/`, `alembic/`, and configuration/assets as the project evolves.

## Development Workflow

1. **Create a branch** for the feature/fix and keep changes scoped.
2. **Understand before changing**: review relevant docs, domain rules, and existing modules.
3. **Implement inward-out safely**: define/extend domain and application ports first, then infrastructure adapters and UI.
4. **Keep configuration externalized**: use `.env` and settings models; never hardcode secrets or environment-specific values.
5. **Add/update tests** alongside behavior changes.
6. **Run quality checks** before committing:
   - `ruff check .`
   - `ruff format .` (or `ruff format --check .` in CI)
   - `mypy src`
   - `pytest`
7. **Document changes** in `docs/` and README when architecture, schema, or workflows evolve.

## Testing Instructions

Run the full test suite:

```powershell
pytest
```

Run with coverage:

```powershell
pytest --cov=dota_tracker --cov-report=term-missing
```

Run static analysis and linting:

```powershell
ruff check .
mypy src
```

Recommended testing strategy:
- **Unit tests**: domain entities/services and application use cases with mocked ports.
- **Integration tests**: SQLAlchemy repositories, Alembic migrations, and OpenDota client behavior (using test DB/HTTP mocking).
- **UI tests**: presentation-layer logic where feasible (view models/controllers), minimizing brittle widget snapshot tests.

## Future Extensions

- Background synchronization jobs and scheduling for periodic OpenDota imports.
- Caching layer for API responses and computed analytics.
- Advanced analytics (hero synergies, lane outcomes, trends, MMR progression insights).
- Export/import of reports (CSV, PDF, images).
- Multi-profile support and team-level analytics.
- Plugin/module system for custom metrics and visualizations.
- Packaging and distribution (PyInstaller/briefcase) with auto-update strategy.
- Observability enhancements (structured logs, metrics, diagnostics panel).

## License

Proprietary. All rights reserved unless a license is explicitly added to this repository.
