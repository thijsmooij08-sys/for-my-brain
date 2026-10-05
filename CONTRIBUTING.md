# Contributing to PolyTrader

Read `AGENTS.md`, `docs/STATE.yaml`, and the active ExecPlan before changing
code. Preserve the Strategy → Signal → Opportunity → PositionSizer →
RiskManager → OrderIntent → ExecutionEngine boundary.

Every change must keep `LIVE_TRADING_ENABLED=false`, use exact `Decimal`
financial arithmetic, and avoid credentials or wallet signing material. Paper
fills must walk the available order book; midpoint fills are not acceptable.

Before opening a pull request, run:

```powershell
backend/.venv/Scripts/python -m pytest backend/tests
backend/.venv/Scripts/python -m ruff check backend
npm --prefix frontend run build
powershell -ExecutionPolicy Bypass -File scripts/verify.ps1
```

Document any new data source, provenance rule, risk boundary, or known
technical debt. Do not copy third-party trading-bot code into the execution
path without a license and security review.
