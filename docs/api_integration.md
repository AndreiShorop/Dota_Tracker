# API Integration: OpenDota

## Overview

Dota Tracker integrates with the [OpenDota API](https://docs.opendota.com/) to ingest players, matches, heroes, and items. The integration is implemented in the **infrastructure layer** behind an application-layer port (e.g., `OpenDotaGateway`) so domain/application logic remains independent of HTTP and provider-specific details.

Primary goals:
- Reliable, typed data retrieval from OpenDota
- Controlled request rates and resilient retries
- Strict response validation before persistence/analytics
- Configurable behavior via environment-driven settings

## OpenDota API Client Design

**Planned location:** `src/dota_tracker/infrastructure/opendota/`

### Components

- **`OpenDotaClient` (low-level HTTP client)**
  - Built on `httpx` (`httpx.Client` for sync, `httpx.AsyncClient` for async).
  - Responsible for: base URL resolution, request building, auth headers/params, timeouts, retries, rate limiting, and raw response handling.
  - Returns validated DTOs or typed response models, not raw `dict`s, across the port boundary.

- **`OpenDotaGateway` (adapter implementing application port)**
  - Translates application requests into OpenDota endpoints and maps responses to application/domain DTOs.
  - Example operations:
    - `get_player(account_id)`
    - `get_player_recent_matches(account_id)`
    - `get_match(match_id)`
    - `get_heroes()`
    - `get_items()` (if sourced from OpenDota/constants endpoints as applicable)

- **Request/Response models**
  - Pydantic v2 models for external API payloads (separate from domain entities and ORM models).
  - Explicit mappers: `OpenDota DTO -> Application/Domain DTO`.

- **Endpoint registry**
  - Centralized path builders (e.g., `/players/{account_id}`, `/players/{account_id}/matches`, `/matches/{match_id}`, `/heroes`) to avoid string scattering.

### Transport and Lifecycle

- Single configured client instance per process/session context where possible (connection reuse).
- Explicit timeout configuration (`OPENDOTA_TIMEOUT_SECONDS`).
- Structured logging (loguru) for request metadata (endpoint, status, latency, attempt) without logging secrets.

## Rate Limiting Strategy

OpenDota enforces rate limits; the client must proactively limit outbound request volume and react to server signals.

### Configuration

- `OPENDOTA_RATE_LIMIT_RPM`: maximum requests per minute (default from `.env.example`, e.g., 60). Tune conservatively and adjust per API key/policy.
- Optional future settings: burst size, per-endpoint limits, concurrency cap.

### Client-side controls

- **Token bucket / sliding window limiter**: Acquire a permit before each request; block/await until a permit is available.
- **Concurrency limiting**: Semaphore to cap in-flight requests (especially for async batch fetches).
- **Backoff on throttling**: If HTTP `429 Too Many Requests` is received, respect `Retry-After` when present; otherwise apply exponential backoff with jitter.
- **Global coordination**: Limiter shared across gateway methods to prevent accidental bursts from parallel sync tasks.

## Retry Logic

Retries apply only to transient failures and must be bounded.

### Configuration

- `OPENDOTA_MAX_RETRIES` (default: 3)
- `OPENDOTA_TIMEOUT_SECONDS` (default: 30)
- Backoff parameters (recommended defaults): base 0.5s, multiplier 2x, max delay 30s, full jitter

### Retryable conditions

- Network errors: connect/read/write timeouts, DNS/transient connection failures (`httpx` transport exceptions).
- HTTP status codes: `429`, `500`, `502`, `503`, `504`.
- Optionally retry idempotent `GET` requests on selected `408` responses.

### Non-retryable conditions

- `400`, `401`, `403`, `404`, `422` and other client/semantic errors (fail fast with typed errors).
- Validation failures after a successful response (indicates schema drift or mapping bug; do not retry blindly except after controlled refresh logic if applicable).

### Behavior

- Exponential backoff with jitter between attempts.
- Honor `Retry-After` for `429`/`503` when provided.
- Log each attempt outcome and final failure reason.
- Propagate a typed exception (e.g., `OpenDotaRateLimitError`, `OpenDotaUnavailableError`, `OpenDotaRequestError`) to the application layer.

## Error Handling

Errors are categorized and translated at the infrastructure boundary:

| Category | Examples | Handling |
| --- | --- | --- |
| Configuration | Missing/invalid base URL, invalid timeout/rate settings | Fail fast at startup/client initialization with clear validation errors |
| Network/Timeout | `httpx.TimeoutException`, connection errors | Retry per policy; raise typed transient error on exhaustion |
| Rate limiting | HTTP 429 | Backoff/retry with `Retry-After`; surface rate-limit error if exhausted |
| HTTP client errors | 4xx (except 429) | No retry; map to `NotFound`, `Unauthorized`, `BadRequest` application errors as appropriate |
| HTTP server errors | 5xx | Retry per policy; raise unavailable error on exhaustion |
| Parsing/Validation | JSON decode errors, schema mismatch | Raise `OpenDotaResponseValidationError` with context (endpoint, field/path when safe) |
| Mapping errors | Missing required fields for domain invariants | Raise explicit mapping/domain-input errors; do not persist partial invalid data |

Rules:
- Never swallow exceptions silently.
- Do not log secrets (API keys, tokens).
- Include correlation/context (endpoint, account/match id, attempt count) in logs and error messages where safe.

## Response Validation

All external data must be validated before use.

### Validation layers

1. **HTTP/transport validation**: status code checks, content-type expectations, JSON decoding.
2. **Schema validation (Pydantic)**: parse OpenDota payloads into strict/explicit response models.
   - Required fields enforced; optional fields typed with defaults/`None`.
   - Tolerant readers where provider adds fields: allow extra fields in raw models (`extra="allow"` or capture in `raw_data`) while keeping normalized fields strict.
3. **Domain/application mapping validation**: convert to internal DTOs/entities and enforce invariants (e.g., valid IDs, non-negative stats, consistent team/win flags).
4. **Persistence constraints**: DB unique/FK/check constraints as final integrity backstop.

### Drift handling

- Detect schema drift via validation errors and structured logs.
- Prefer updating response models/mappers over loosening core domain invariants.
- Store selected raw payload snapshots (`JSONB`) only when justified for traceability/debugging.

## Sync vs Async Strategy

### Recommended approach

- **Start with synchronous I/O for simplicity** in desktop-driven workflows and background jobs that run sequentially, using `httpx.Client` and a shared rate limiter.
- **Adopt async (`httpx.AsyncClient`) selectively** for high-volume batch ingestion (e.g., syncing many matches) where concurrency improves throughput within rate limits.
- **Do not mix paradigms ad hoc**: keep sync and async clients/gateways clearly separated (e.g., `OpenDotaClientSync` / `OpenDotaClientAsync` or explicit method sets).

### Decision guidelines

| Scenario | Preferred | Rationale |
| --- | --- | --- |
| Single player/match fetch from UI action | Sync | Simple control flow, easier integration with Qt signals/slots |
| Bulk historical sync (many matches/players) | Async (bounded concurrency) | Better throughput while respecting RPM/concurrency caps |
| Periodic scheduled sync | Sync or Async | Choose based on volume; keep jobs idempotent and observable |
| Tests | Sync + mocked transport | Deterministic; async tests via `pytest-asyncio` when needed |

### UI integration notes (PySide6)

- Never block the Qt event loop with network calls.
- Run sync API work in a worker thread (`QThread`/`QRunnable`) or use async integration patterns deliberately.
- Communicate progress/results/errors back to UI via signals and application-level DTOs.

## Configuration

All integration settings are environment-driven (see `.env.example`) and loaded via typed settings:

- `OPENDOTA_BASE_URL` (default: `https://api.opendota.com/api`)
- `OPENDOTA_API_KEY` (optional; increases rate limits if provided)
- `OPENDOTA_TIMEOUT_SECONDS` (default: `30`)
- `OPENDOTA_MAX_RETRIES` (default: `3`)
- `OPENDOTA_RATE_LIMIT_RPM` (default: `60`)

Security and operations:
- Never hardcode API keys or secrets.
- Validate settings on startup (URL format, positive numeric ranges).
- Allow environment-specific overrides without code changes.
