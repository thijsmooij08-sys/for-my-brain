# Phase 1 ExecPlan

## Objective
Deliver a verified public-data-to-realistic-paper-trading pipeline while making real Polymarket submission impossible.

## Scope / non-goals
M1–M10 and P1-001–P1-030 only. Excludes streams, backtests, stock venues, MCP servers, learning, wallets, authenticated clients, and live orders.

## Invariants
All `INV-001` through `INV-018` in `docs/INVARIANTS.md` apply.

## Architecture
FastAPI/Pydantic/SQLAlchemy/Alembic backend, React dashboard, SQLite development storage, official `polymarket-client` adapter, Decimal canonical financial domain.

## Milestones and progress
- M1 Control Plane — PASS: required router/documents, ADR, and ExecPlan created.
- M2 Development Environment — PASS: Python 3.12 venv, pinned backend dependencies, React/Vite app/npm lock, Alembic initial SQLite migration, setup, and single-command quality gate verified.
- M3 Public Polymarket Adapter — PASS: official SDK 0.12.0 installed; public smoke verified real market, Yes/No token identity, normalized CLOB book, and token-aware scanner.
- M4 Domain + Persistence — PASS: canonical order-book domain, auditable SQLite fills, Alembic migration, Decimal state projection, and API state reconstruction verified.
- M5 Scanner + Development Strategy — PASS: explicitly non-validated DevelopmentStrategy, Signal→Opportunity transformation, conservative sizing, public scanner, and workflow integration tested.
- M6 Sizing + Risk — PASS: deterministic hard limits, dynamic paper-engine exposure, duplicate protection, liquidity/staleness/spread/daily-loss/kill checks, and workflow gating tested.
- M7 Paper Execution + Accounting — PASS: Decimal book walking, partial fills, fees, cash, cost basis, realized/unrealized P&L, executable-bid equity, ownership, persisted fills, and reconciliation tested.
- M8 API + Dashboard — PASS: state endpoints use persistence, live read-only `/markets` works, and browser DOM verification shows public markets plus PAPER/no-real-orders messaging.
- M9 Validation — PASS: quality gate, public smoke, clean startup, browser verification, integration check, and adversarial source/secret review completed.
- M10 Final Review — PASS: Phase 1 acceptance audit completed; live order path remains explicitly impossible.

### GitHub ecosystem preparation (completed before further Phase 1 implementation)

The approved research/data repositories are represented in `docs/integrations/GITHUB_ECOSYSTEM.md`. Safe libraries are installed in the opt-in `backend[research]` extra and connected only through `polytrader.research` adapters. Verified versions on 2026-10-04: Alpaca 0.44.0, pandas 2.3.3, Polars 1.44.2, scikit-learn 1.9.1, statsmodels 0.15.0, PyPortfolioOpt 1.6.0, Riskfolio-Lib 7.4.0, quantstats 0.0.86, VectorBT 0.28.5, Plotly 5.24.1, and prometheus-client 0.26.0. MLflow, FinRL, archived Zipline, Alpaca MCP, and SEC-EDGAR MCP are explicitly reviewed and disabled, not silently treated as installed or trusted execution components.

## Acceptance criteria
| ID | Status | Evidence |
| --- | --- | --- |
| P1-001 | PASS | Editable install with the pinned research extra completed successfully; commands are recorded in STATE and README. |
| P1-002 | PASS | Uvicorn startup observed. |
| P1-003 | PASS | Vite development server startup observed at `127.0.0.1:5173`. |
| P1-004 | PASS | Official SDK smoke retrieved market id 559651. |
| P1-005–P1-008 | PASS | Live SDK smoke retrieved a market, its `outcomes.yes/no.token_id`, and a 24-bid/131-ask CLOB book. |
| P1-009 | PASS | Clean backend/frontend startup plus browser DOM verification showed live market rows (559651–559660), Open status, PAPER mode, and the no-real-orders banner. |
| P1-010–P1-012 | PASS | Offline pipeline and integrated workflow tests. |
| P1-013 | PASS | Offline deterministic approval/rejection tests cover hard limits, stale data, liquidity, daily loss, duplicate, and kill switch. |
| P1-014 | PASS | Tested OrderIntent construction requires explicit risk approval. |
| P1-015–P1-016 | PASS | Order-book book walking and partial-depth tests. |
| P1-017–P1-018 | PASS | Exact cash/position and realized P&L tests. |
| P1-019–P1-021 | PASS | Offline exact unrealized/equity and SQLite fill persistence tests. |
| P1-022 | PASS | Portfolio, positions, and orders endpoints now project from the auditable SQLite fill repository using Decimal arithmetic; API tests remain green. |
| P1-023–P1-024 | PASS | Duplicate and ownership tests. |
| P1-025 | PASS | No wallet or API credentials are required by setup, tests, smoke, or paper workflow. |
| P1-026 | PASS | `submit_live_order()` raises `LiveTradingDisabledError`; no secure client or live order API is referenced. |
| P1-027 | PASS | `scripts/verify.ps1` secret scan passed. |
| P1-028 | PASS | Standard 19-test suite passed without live credentials. |
| P1-029 | PASS | Core tests passed offline; public network access is isolated to the separate smoke command. |
| P1-030 | PASS | STATE was updated from the current 19-test, quality-gate, startup, browser, and public-smoke evidence. |

## Validation plan
`scripts/verify.ps1` will run backend format/lint/type/tests, migration validation, frontend checks/build, and secret scan. `scripts/smoke_polymarket.ps1` will be a separate public read-only smoke test. Backend and frontend startup will be observed directly.

## Decisions / discoveries
- Official `polymarket-client` 0.12.0 is selected for the isolated public adapter.
- Linked GitHub access is unavailable; public GitHub research is documented in `docs/integrations/GITHUB_ECOSYSTEM.md`.
- No GitHub ecosystem component beyond the official SDK is warranted in Phase 1.
- Intelligence expansion integrated as future architecture only: evidence/provenance, feature families, multi-asset intelligence engines, capital policy, exposure graph, stress scenarios, signal fusion, and multiple-hypothesis standards are assigned to Phases 2–7; no future module was implemented in Phase 1.
- Fresh checks: 19 offline backend tests pass; `scripts/verify.ps1` is green; clean Uvicorn/Vite startup and browser DOM verification showed live market rows; public SDK smoke fetched market id 559651 plus Yes token `323382…993401` and a live CLOB book.

## Definition of done
Every M1–M10 validation has succeeded; P1-001–P1-030 are freshly verified; STATE contains only evidence-backed facts; no code path can submit a real order. Phase 1 is COMPLETE. Phase 2 is documented in the roadmap but has not been started.
