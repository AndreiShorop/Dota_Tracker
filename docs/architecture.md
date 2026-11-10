# Architecture

## Overview

Dota Tracker is structured using **Clean Architecture** (ports and adapters) to keep business logic independent from frameworks, UI, database engines, and external APIs. This enables testability, maintainability, and safe evolution of infrastructure and presentation concerns.

## Layer Diagram

```text
+---------------------------------------------------------------------+
|                        Presentation Layer                           |
|                  (PySide6 UI, Views, ViewModels)                    |
|  - Renders data, captures user input, triggers use cases            |
+-----------------------------------+---------------------------------+
                                    |
                                    v  (calls use cases / DTOs)
+---------------------------------------------------------------------+
|                        Application Layer                            |
|                 (Use Cases, Ports, Orchestration)                   |
|  - Coordinates workflows                                            |
|  - Defines interfaces/ports for persistence & external services      |
+-------------------------+--------------------------+----------------+
                          |                          |
                          v                          v
+-------------------------------+      +-------------------------------+
|         Domain Layer          |      |         Analytics Layer       |
| (Entities, Value Objects,     |      | (Metrics, Aggregations,       |
|  Domain Services, Rules)      |      |  Pandas/NumPy/Matplotlib)     |
|  - Pure business logic        |      |  - Consumes app/domain data   |
+---------------+---------------+      +---------------+---------------+
                ^                                      ^
                | implements/uses domain types         |
                |                                      |
+---------------+--------------------------------------+--------------+
|                        Infrastructure Layer                         |
| (SQLAlchemy/Alembic, PostgreSQL, OpenDota HTTP Client, Config,    |
|  Logging, File/OS adapters)                                         |
|  - Implements application ports (repositories, gateways, etc.)      |
+---------------------------------------------------------------------+

Dependency direction (compile-time intent):
  Presentation  -->  Application  -->  Domain
                         ^                 ^
                         |                 |
                    Analytics       Infrastructure (adapters)

Inner layers must not depend on outer layers.
```

## Dependency Rule

- Source code dependencies point **inward** toward the domain.
- **Domain**: no imports from application, infrastructure, presentation, or analytics frameworks.
- **Application**: depends on domain and defines ports; no imports from UI or concrete infrastructure.
- **Infrastructure**: depends on application ports/domain types and external libraries (SQLAlchemy, httpx, etc.) to implement adapters.
- **Presentation**: depends on application use cases/DTOs and UI framework; no direct DB/HTTP logic.
- **Analytics**: may depend on domain/application data structures; avoid coupling to persistence or UI implementations.

Enforcement strategies: package boundaries, import-lint rules (future), code reviews, and tests that mock ports.

## Domain Layer

**Location (planned):** `src/dota_tracker/domain/`

**Responsibilities:**
- Core business concepts: players, matches, heroes, items, and player-match performance.
- Entities with identity and lifecycle (e.g., `Player`, `Match`).
- Value objects for immutable concepts (e.g., identifiers, durations, K/D/A, match outcome).
- Domain services for rules that do not naturally belong to a single entity.
- Domain exceptions and invariants.

**Characteristics:**
- Pure Python, framework-agnostic.
- No I/O, no SQLAlchemy models, no HTTP calls, no Qt dependencies.
- Easily unit-testable.

## Application Layer

**Location (planned):** `src/dota_tracker/application/`

**Responsibilities:**
- Use cases / interactors (e.g., sync player matches, compute player summary, import heroes/items catalog).
- Orchestration of domain logic and external operations via ports.
- Transaction boundaries and workflow policies (at an abstract level).
- Input/output DTOs and mapping between transport/persistence models and domain models.
- Port definitions (interfaces/protocols) for repositories and gateways.

**Examples of ports:**
- `PlayerRepository`, `MatchRepository`, `HeroRepository`, `ItemRepository`
- `OpenDotaGateway` (fetch players/matches/heroes/items)
- `UnitOfWork` / transaction manager (if adopted)
- `Clock`, `SettingsProvider` (as needed)

## Infrastructure Layer

**Location (planned):** `src/dota_tracker/infrastructure/`

**Responsibilities:**
- Concrete implementations of application ports (adapters).
- **Persistence:** SQLAlchemy ORM models/mappings, repository implementations, session management, Alembic migrations.
- **External APIs:** OpenDota HTTP client (httpx), request/response mapping, retry/rate-limit handling.
- **Configuration:** pydantic-settings loaders, `.env`/YAML integration.
- **Logging/observability:** loguru configuration and sinks.
- **System adapters:** file system, caching, serialization details.

**Rules:**
- Keep external schemas and ORM models separate from domain entities (use mappers).
- Handle infrastructure-specific errors and translate them to application/domain-relevant errors at boundaries.

## Presentation Layer

The local FastAPI web adapter exposes player-list, dashboard, and sync endpoints and serves bundled static assets. Controllers call application use cases; a request-scoped composition root wires the SQLAlchemy dashboard read port and existing sync workflow, closes database sessions and the OpenDota client, and translates infrastructure failures into safe API errors. Dashboard projections join internal persistence keys while exposing OpenDota match and hero identifiers. The server defaults to loopback and has no authentication; it is not a public-facing deployment configuration.

**Location (planned):** `src/dota_tracker/presentation/`

**Responsibilities:**
- PySide6 desktop UI: windows, dialogs, widgets, views, and navigation.
- Presentation models/view models/controllers to adapt application DTOs for display.
- User input validation at UI level (format/UX), delegating business validation to application/domain.
- Triggering use cases and rendering results, loading states, and errors.

**Rules:**
- No direct database queries or HTTP calls.
- No business rules embedded in widgets.
- Depend on abstractions/use cases to keep UI testable and replaceable.

## Analytics Layer

**Location (planned):** `src/dota_tracker/analytics/`

**Responsibilities:**
- Computation of derived metrics and aggregations (win rates, trends, role/hero performance, timelines).
- Data preparation pipelines using pandas/numpy.
- Visualization generation with matplotlib (charts/plots for embedding in UI or export).
- Reusable, deterministic analytics functions operating on DTOs/domain data snapshots.

**Rules:**
- Keep analytics logic pure where possible (input data in, results out).
- Avoid direct I/O; data loading/saving should go through application/infrastructure ports.
- Separate computation from rendering concerns when feasible.

## Ports and Adapters

**Ports** are interfaces/protocols defined by the application layer that express required capabilities without specifying technology (e.g., "fetch match by id", "persist player matches"). They enable dependency inversion.

**Adapters** are infrastructure/presentation implementations that fulfill ports:
- **Driving adapters (primary):** UI controllers/actions that invoke application use cases.
- **Driven adapters (secondary):** PostgreSQL repositories, OpenDota gateway, cache, clock, etc.

**Benefits:**
- Swap implementations (e.g., mock repositories in tests, different data sources).
- Isolate framework churn from core logic.
- Improve unit/integration testing by injecting fakes or in-memory adapters.

**Guidelines:**
- Define ports around use-case needs, not database tables or API endpoints.
- Keep port contracts stable and explicit (types, error semantics, idempotency expectations).
- Map at boundaries: DTO/domain <-> ORM/API schemas.
