# Framework Research Boundaries Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the safe, research-only knowledge from NautilusTrader, Hummingbot, Freqtrade, and Kronos without importing live execution, credentials, or venue connectors.

**Architecture:** Extend the existing external research catalog as the executable allow/deny boundary. Document selectively adopted patterns and future real-money transition gates in durable project documentation and workspace memory. No third-party framework becomes a runtime dependency.

**Tech Stack:** Python 3.11+, dataclasses, pytest, Markdown/YAML, existing catalog/import boundary.

**Spec:** `AGENTS.md`, `docs/INVARIANTS.md`, `docs/security/LIVE_READINESS.md`, `docs/integrations/EXTERNAL_RESEARCH_REVIEW_2026-10-05.md`.

## Global Constraints

- Exact `Decimal` financial math remains authoritative.
- External frameworks remain research/reference sources only.
- No credentials, wallet keys, signers, live clients, or order endpoints are added.
- `LIVE_TRADING_ENABLED=false` remains authoritative.
- RiskManager and the paper execution engine remain the only execution authorities.

## Review Focus

- Live-capable framework entries must be rejected by the replay importer.
- Research-only entries must never expose execution authority.
- Kronos OHLCV forecasting must not be represented as a Polymarket order signal.
- Future real-money notes must be gates and prerequisites, not activation instructions.
- Existing catalog imports and all prior tests must remain backward compatible.

### Task 1: Catalog boundaries

**Files:**
- Modify: `backend/src/polytrader/research/external_catalog.py`
- Test: `backend/tests/test_external_research.py`

- [x] Write failing tests for four new catalog entries and their runtime boundaries.
- [x] Add NautilusTrader, Hummingbot, Freqtrade, and Kronos entries with accepted research patterns and explicit decisions.
- [x] Run focused and full backend tests.

### Task 2: Documentation and transition memory

**Files:**
- Modify: `docs/integrations/EXTERNAL_RESEARCH_REVIEW_2026-10-05.md`
- Modify: `docs/INDEX.md`
- Modify: `docs/STATE.yaml`
- Modify: workspace memory `memory/DECISIONS.md`

- [x] Record what was adopted, what remains isolated, and what was rejected.
- [x] Record real-money transition knowledge as future gates only.
- [x] Update state only after verification.

### Task 3: Verification

- [x] Run backend tests, Ruff, full verification, public smoke, research checks, and Compose validation.
- [x] Confirm live execution remains disabled and repository is clean.
- [ ] Commit and publish.
