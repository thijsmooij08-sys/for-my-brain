# Market Replay Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve research realism with Polymarket fee schedules, resolution lock-up metadata, conservative queue estimates, and replay clock-quality diagnostics.

**Architecture:** Add pure simulation value objects and analyzers around the existing replay/fill contracts. These features are research-only: they produce estimates and metrics, never orders or execution authority. All monetary values use `Decimal`.

**Tech Stack:** Python 3.11+, existing simulation modules, Decimal, datetime, pytest, Ruff, Pyright.

**Spec:** `AGENTS.md`, `docs/domain/EXECUTION.md`, `docs/backtesting/BACKTESTING.md`, `docs/INVARIANTS.md`.

## Global Constraints

- Exact `Decimal` financial math remains authoritative.
- RiskManager and the paper execution engine remain unchanged authorities.
- No live client, signer, credential, or order endpoint is introduced.
- Queue and resolution outputs are estimates/metadata only and cannot mutate accounting.
- Existing `ReplayDataset` serialization remains backward compatible.

## Review Focus

- Fee prices at 0, 0.5, and 1 must remain exact and bounded.
- Resolution dates must be timezone-aware and settlement cannot precede resolution.
- Queue estimates must never produce negative fills or exceed traded volume.
- Replay quality must expose out-of-order and collection-lag evidence instead of silently hiding it.
- New research values must not appear as executable order intents.

---

### Task 1: Fee and resolution models

**Files:**
- Create: `backend/src/polytrader/simulation/market_costs.py`
- Test: `backend/tests/test_market_costs.py`
- Modify: `backend/src/polytrader/simulation/__init__.py`

- [x] Write failing tests for Decimal V2 fee behavior, maker exemption, invalid prices, and resolution/dispute lock-up validation.
- [x] Implement `PolymarketFeeModel` and `ResolutionSchedule` as immutable research value objects.
- [x] Run focused tests and the full backend suite.

### Task 2: Queue and replay-quality diagnostics

**Files:**
- Create: `backend/src/polytrader/simulation/microstructure.py`
- Create: `backend/src/polytrader/simulation/quality.py`
- Test: `backend/tests/test_market_replay_hardening.py`
- Modify: `backend/src/polytrader/simulation/__init__.py`

- [x] Write failing tests for conservative queue fill estimates, timestamp regressions, duplicate sequences, and collection-lag summaries.
- [x] Implement queue estimates and a replay quality analyzer without third-party runtime dependencies.
- [x] Keep diagnostics read-only and non-actionable.
- [x] Run focused tests and the full backend suite.

### Task 3: Documentation, state, and verification

**Files:**
- Create: `docs/backtesting/MARKET_REPLAY_HARDENING.md`
- Modify: `docs/INDEX.md`
- Modify: `docs/STATE.yaml`
- Modify: active ExecPlan status

- [x] Document what was adopted from each reviewed project and what remains rejected.
- [x] Run Ruff, Pyright, `scripts/verify.ps1`, public-data smoke, research checks, and Compose validation.
- [x] Confirm live execution remains disabled and Docker remains in paper mode.
- [x] Update `docs/STATE.yaml` only with freshly verified evidence.
- [x] Commit and publish.
