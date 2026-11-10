# AGENTS.md

## Project Purpose

Dota Tracker is a professional desktop analytics application for Dota 2. It provides a PySide6 UI backed by PostgreSQL to ingest data from OpenDota, persist it reliably, and deliver analytics and visualizations for players, matches, heroes, and items.

## Technology Stack

- **Language:** Python 3.13
- **UI:** PySide6 (Qt for Python)
- **Database:** PostgreSQL 16
- **ORM/Migrations:** SQLAlchemy 2.x, Alembic
- **Validation/Settings:** Pydantic v2, pydantic-settings
- **HTTP Client:** httpx
- **Analytics:** pandas, numpy, matplotlib
- **Logging:** loguru
- **Configuration:** `.env`, PyYAML
- **Testing/Quality:** pytest, pytest-asyncio, pytest-cov, ruff, mypy (strict)

## Architecture Rules

Follow **Clean Architecture** with dependencies pointing inward:

- **Presentation → Application → Domain**
  - UI (PySide6) depends on application use cases/DTOs/ports, never on infrastructure details.
  - Application orchestrates use cases and defines ports (interfaces); it depends on domain abstractions.
  - Domain contains entities, value objects, and business rules; it has **no** dependencies on frameworks, UI, DB, or HTTP clients.
- **Infrastructure implements ports**
  - Database repositories, OpenDota clients, configuration, logging adapters, and external integrations live in infrastructure and implement application ports.
  - Infrastructure may depend on application/domain types but must not leak framework-specific types across port boundaries.
- **Analytics layer**
  - Consumes domain/application outputs for metrics and visualization; keep it decoupled from UI and persistence implementations where possible.

**Do not:**
- Import infrastructure modules into domain or application core logic.
- Put business rules in UI widgets or ORM models.
- Bypass ports/use cases from presentation to talk directly to the database or external APIs.

## Coding Standards

- **Type hints:** Required everywhere (functions, methods, attributes, public APIs). Maintain compatibility with strict mypy.
- **Docstrings:** Provide clear docstrings for public modules, classes, and functions describing purpose, inputs, outputs, and important behavior/errors.
- **Naming:** Use meaningful, explicit names. Prefer clarity over brevity. Follow Python conventions (`snake_case`, `PascalCase`, `UPPER_SNAKE_CASE`).
- **Design:** Small, focused classes and functions (single responsibility). Prefer composition over inheritance. Avoid god objects and giant modules/classes.
- **Error handling:** Use explicit, typed exceptions. Fail fast on invalid state; do not silently swallow errors.
- **Immutability where practical:** Prefer value objects/dataclasses/Pydantic models for data transfer and domain values.
- **No duplication:** Reuse existing abstractions/utilities; refactor shared logic instead of copying.
- **Comments:** Add comments only when necessary to explain non-obvious intent or constraints.
- **Formatting/linting:** Keep code compliant with ruff (line length 100) and project conventions.

## Testing Expectations

- **Write/update tests** for all behavior changes (domain rules, use cases, adapters, and critical UI logic where feasible).
- **Test levels:**
  - **Unit tests:** Domain and application logic with mocked ports; fast and deterministic.
  - **Integration tests:** Database repositories/migrations and HTTP client adapters using test databases and mocked HTTP responses.
  - **Regression tests:** Add tests reproducing fixed bugs.
- **Quality gates:** `pytest`, `ruff check .`, and `mypy src` must pass before considering work complete.
- **Coverage:** Aim for meaningful coverage of critical paths; prefer testing behavior and edge cases over chasing percentages.

## Configuration Rules

- **No hardcoded secrets:** Never commit API keys, passwords, tokens, or connection strings.
- **Environment-driven config:** Load runtime configuration from `.env`/environment variables via typed settings (pydantic-settings). Provide safe defaults only where appropriate.
- **Templates:** Keep `.env.example` up to date with required variables (without real secrets).
- **Separation by environment:** Support development/test/production configurations without code changes.
- **Validation:** Validate configuration at startup and fail with clear errors when required settings are missing or invalid.
- **Logging:** Do not log secrets or sensitive personal data; redact where necessary.

## Working Agreements

- Understand existing architecture and patterns before implementing changes.
- Prefer minimal, well-scoped changes that preserve layer boundaries.
- Document significant architectural, schema, or integration changes in `docs/` and `README.md`.
