# PolyTrader

PolyTrader is a safe, modular multi-asset intelligence and Polymarket paper-trading foundation. Phases 1–10 are complete: adaptive-live architecture remains strictly fail-closed over verified data, simulation, intelligence, paper trading, learning, and shadow validation; real-money execution remains impossible.

Read `docs/STATE.yaml` and the active ExecPlan first. Use `docs/INDEX.md` to route to detailed documentation. Phases 1–10 remain complete and must stay green.

Non-negotiables: exact `Decimal` financial math; Strategy → Signal → Opportunity → PositionSizer → RiskManager → OrderIntent → ExecutionEngine; Risk cannot be bypassed; no naked selling; book-walking paper fills only; no secrets or wallet credentials; live trading disabled in code.

Commands: `backend/.venv/Scripts/python -m pytest backend/tests`, `backend/.venv/Scripts/python -m ruff check backend`, and `npm --prefix frontend run build`. Full verification: `scripts/verify.ps1`; public-data smoke: `scripts/smoke_polymarket.ps1`; research integrations: `scripts/check_research_integrations.py`. Local target: `docker compose up --build` (Docker required; paper mode is forced).
