# Phase 10 ExecPlan — Adaptive-Live Architecture (Activation Disabled)

## Objective

Build the adaptive allocation, learning, promotion, rollback, and control
surfaces needed for a future live-capable system while keeping actual
real-money activation behind a separate explicit authorization gate.

## Non-negotiable gates

- `LIVE_TRADING_ENABLED=false` remains authoritative.
- Learning may not raise capital limits, weaken loss limits, disable breakers,
  bypass RiskManager or eligibility, or grant live execution authority.
- All allocation outputs are research artifacts until deterministic controls
  accept them.
- Phases 1–9 remain green.

## Milestones

- P10-A research-only strategy allocation proposals
- P10-B promotion, rollback, and allocation audit records
- P10-C adaptive-control API and observability
- P10-D adversarial learning/risk boundary tests
- P10-E final regression and documentation audit

## Scope exclusions

No real order submission, live activation, signer loading, wallet
authentication, or automatic capital-limit changes.

## Verification

Focused learning tests, complete regression, public-data smokes, Docker health,
secret scan, and explicit proof that learning cannot authorize execution.

## Progress

- P10-A complete: `ResearchAllocator` produces bounded Decimal strategy-weight
  proposals only after minimum samples, positive net P&L, and drawdown gates.
  It exposes `execution_authority=False` and cannot change RiskManager or
  capital limits.
- P10-B complete: `AllocationLedger` stores append-only, hash-chained
  allocation decisions with no execution authority.
- P10-C complete: research-only learning status and allocation proposal API
  endpoints expose bounded decisions and audit hashes without touching risk or
  execution.
- P10-D complete: adversarial tests prove weak candidates are rejected, weights
  are capped, and learning responses cannot grant execution authority.
- P10-E complete: full regression, public-data smokes, research integration
  checks, Docker/Grafana health, secret scan, and documentation audit passed.

## Final verification record

- `scripts/verify.ps1`: passed; 94 backend tests, Ruff, Pyright, Alembic,
  frontend build, and secret scan.
- `scripts/smoke_polymarket.ps1`: passed with a current public market/book.
- `scripts/smoke_polymarket_stream.ps1`: passed with a public book event.
- `scripts/check_research_integrations.py`: passed, including isolated OpenBB,
  Nasdaq Data Link, Feast, and Prefect checks.
- Docker paper worker, preflight, learning status, and Grafana health passed.
- Real-order submission remains impossible; all learning outputs report
  `execution_authority=false` and `live_execution=false`.
