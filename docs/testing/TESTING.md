# Testing

Offline tests are deterministic and require neither public internet nor credentials. Live public-data smoke tests are separate and read-only. Required accounting tests cover exact Decimal purchases, average cost, partial/complete exits, fees, P&L, equity, and ownership. Required risk tests cover hard limits, stale data, liquidity/spread, duplicate actions, kill switch, and live execution prohibition.

Run the consolidated gate with `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`. It runs Ruff, offline tests, Pyright, Alembic upgrade, frontend build, and a committed-secret assignment scan. Run `backend/.venv/Scripts/python scripts/smoke_polymarket.py` separately for live read-only public data.
