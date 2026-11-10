# Dota Tracker

Dota Tracker is a professional desktop analytics application for Dota 2. It combines a PySide6-based user interface, PostgreSQL-backed persistence, and a clean architecture foundation to support reliable match analysis, player performance tracking, and extensible analytics workflows.

## Features

- **Desktop analytics UI**: Native desktop experience built with PySide6 for responsive, local-first workflows.
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

## Quick Start Guide

### Prerequisites

- **Python**: 3.13.x
- **pip**: latest recommended (`python -m pip install --upgrade pip`)
- **Docker** and **Docker Compose** (for local PostgreSQL)
- **Git**

### 1. Clone and configure environment

```powershell
git clone <repository-url> dota-tracker
cd dota-tracker
Copy-Item .env.example .env
```

Edit `.env` and set secure database credentials and any OpenDota settings as needed.

### 2. Start PostgreSQL with Docker Compose

```powershell
docker compose up -d
docker compose ps
```

The `dota-postgres` service exposes PostgreSQL on `localhost:5432` and includes a health check.

### 3. Create a virtual environment and install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e .[dev]
```

### 4. Run database migrations (when Alembic is configured)

```powershell
alembic upgrade head
```

### 5. Run the application

```powershell
python -m dota_tracker
```

> Note: Application entry points, UI screens, and data sync workflows will be implemented within the `src/dota_tracker` package following the architecture described below.

## Project Structure

```text
Dota_Tracker/
├─ .env.example
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
