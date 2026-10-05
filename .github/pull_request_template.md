## PolyTrader change review

### Safety checklist

- [ ] This change preserves `LIVE_TRADING_ENABLED=false` and PAPER-only execution.
- [ ] No wallet key, signer, API secret, password, or session token is included.
- [ ] Strategy, opportunity, sizing, risk, execution, accounting, and learning boundaries remain separate.
- [ ] RiskManager remains the final authority for paper order intents.
- [ ] No naked sell or fictional midpoint fill was introduced.

### Verification

- [ ] Backend tests and Ruff passed.
- [ ] Pyright and Alembic checks passed.
- [ ] Frontend build passed.
- [ ] Relevant public-data, Docker, or research checks passed.

### Summary

Describe the change, affected boundaries, and any known technical debt.
