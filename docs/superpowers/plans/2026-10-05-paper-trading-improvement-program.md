# Paper Trading Improvement Program

## Goal

Complete and verify the seven PolyTrader improvement workstreams while keeping
the system paper-only, risk-gated, and exact-Decimal:

1. reliable paper exits and a complete buy → manage → sell → account loop;
2. executable-liquidity and opportunity-quality filters;
3. closed-trade performance and calibration metrics;
4. live dashboard activity, equity, and rejection visibility;
5. prospective historical order-book accumulation and replay coverage;
6. controlled research experiments and Champion/Challenger boundaries;
7. Docker, backup, alert, and automated-verification hardening.

## Non-negotiables

- Strategy → Signal → Opportunity → PositionSizer → RiskManager → OrderIntent → ExecutionEngine remains authoritative.
- Sells use owned inventory and book walking; no naked selling or manual live-order path.
- `LIVE_TRADING_ENABLED=false` remains authoritative.
- No wallet keys, signers, or provider credentials are added.
- Each workstream requires focused tests, full relevant verification, and a fresh `docs/STATE.yaml` update.

## Task 1 — Position management exits

- [x] Add a regression test proving an existing position can exit when the new cycle has no BUY signal.
- [x] Manage positions present at cycle start independently of entry candidates.
- [ ] Verify against the rebuilt Docker paper worker using current public books.
- [ ] Record whether any live paper exits occur; do not treat zero exits as a failure when no book meets the configured threshold.

## Task 2 — Opportunity quality

- [ ] Add explicit rejection reasons and metrics for spread, depth, freshness, and resolution-risk filters.
- [ ] Keep thresholds deterministic and configurable without weakening hard risk limits.

## Task 3 — Performance evidence

- [x] Expose realized P&L, total fees, and closed-trade sample size from the auditable fill ledger.
- [x] Keep zero-closed-trade state distinct from a zero-percent win rate in the API and dashboard.
- [x] Add drawdown and expectancy by closed trade; slippage and calibration remain to be added.

## Task 4 — Dashboard observability

- [x] Surface paper-scan rejection reasons and ledger performance summary in the live dashboard.
- [x] Add a recent paper fills feed from the ledger; equity history remains to be wired to historical snapshots.
- [ ] Verify all controls through the browser against the Docker build.

## Task 5 — Historical evidence

- [ ] Extend prospective capture/replay coverage and document unavailable backfill clearly.

## Task 6 — Controlled research

- [ ] Add research-only experiment artifacts and Champion/Challenger comparison without execution authority.

## Task 7 — Operations

- [ ] Verify restart, backup, alert, and full verification workflows; document remaining deployment assumptions.

## Verification commands

```powershell
backend/.venv/Scripts/python -m pytest backend/tests
backend/.venv/Scripts/python -m ruff check backend
npm --prefix frontend run build
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
powershell -ExecutionPolicy Bypass -File scripts/smoke_polymarket.ps1
backend/.venv/Scripts/python scripts/check_research_integrations.py
docker compose config --quiet
```
