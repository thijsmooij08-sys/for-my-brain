# Phase 8 ExecPlan — Live-Readiness Engineering (Submission Disabled)

## Objective

Build and verify the security, eligibility, reconciliation, account-sync, user-stream, and execution-state-machine boundaries required for a future live venue integration, while keeping all real-order submission impossible. This phase may model authenticated capabilities, but it must not initialize a signer from user material, ask for credentials, or send an order.

## Non-negotiable gates

- `LIVE_TRADING_ENABLED=false` is authoritative and cannot be overridden by configuration, learning, UI, or an external adapter.
- No wallet private key, API secret, password, OAuth code, or signing material is requested, persisted, logged, or loaded by tests.
- Every live execution path fails closed before network submission.
- Account snapshots, user-stream events, eligibility decisions, and reconciliation results are typed, timestamped, provenance-aware, and auditable.
- Reconciliation and production circuit breakers are deterministic and block on uncertainty.
- Phases 1–7 remain green; paper execution and accounting continue to use exact `Decimal` math and book-walking fills.

## Milestones

- P8-A secure configuration and signer boundary
- P8-B authenticated-capability and account-sync contracts using redacted test doubles only
- P8-C user-stream event normalization and sequence-gap detection
- P8-D eligibility, reconciliation, and production circuit-breaker decisions
- P8-E fail-closed live execution state machine and API safety exposure
- P8-F complete regression, adversarial security review, and documentation gate

## Scope exclusions

No live SDK client initialization, signer loading, wallet connection, authenticated API call, real order submission, live activation switch, or Phase 9/10 work is allowed in this plan.

## Verification

Focused unit/property tests, static checks, complete regression, public read-only Polymarket smoke tests, Docker health, and a repository secret scan are required before marking this phase complete.

## Progress

- P8-A complete: `LiveSafetyConfig`, forbidden environment checks, and redacted signer/capability boundary are implemented.
- P8-B complete: typed `AccountSnapshot` and redacted authenticated-capability contracts are implemented; no secure client or credential loader exists.
- P8-C complete: user-stream normalization, payload hashing, replay handling, and sequence-gap detection are implemented.
- P8-D complete: exact Decimal reconciliation, freshness/eligibility checks, deterministic circuit-breaker reasons, and append-only hash-chained readiness journal are implemented.
- P8-E complete: the disabled live-execution state machine and redacted `/api/v1/live-readiness` endpoint are implemented and verified in the rebuilt Docker API.
- P8-F complete: adversarial review, full regression, public-data smoke tests, research-integration checks, Docker health, secret scan, and documentation audit passed. The paper engine restores in-memory state from the append-only fill ledger after restart, so subsequent paper cycles remain available without any venue submission path.

## Paper observability extension

The React dashboard and Grafana now expose API-backed paper equity, cash,
fill count, closed-trade wins/losses, and win rate. `POST /api/v1/paper/cycle`
runs one bounded public-data cycle through the existing deterministic paper
pipeline. It never submits a venue order. The official SDK's verbose
`active=True ... accepting_orders=True` state is normalized by the paper loop,
and the execution engine restores from the ledger after restart. Cycles fail
closed on stale, invalid, incomplete, or over-limit data.

## Final verification record

- `scripts/verify.ps1`: passed; 83 backend tests, Ruff, Pyright, Alembic, frontend build, and secret scan.
- `scripts/smoke_polymarket.ps1`: passed with a current public market and order book.
- `scripts/smoke_polymarket_stream.ps1`: passed with a public `book` stream event.
- `scripts/check_research_integrations.py`: passed for the main research stack and isolated Feast, Prefect, Nasdaq Data Link, and OpenBB environments.
- Docker API: rebuilt and verified health, paper cycle, paper performance, and redacted disabled live-readiness state.
- Grafana: internal health 200 and `PolyTrader Overview` dashboard provisioned.
- Real order submission: impossible; `LIVE_TRADING_ENABLED=false`, no signer, credentials, or live client loaded.
