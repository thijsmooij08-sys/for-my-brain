# Phase 2 Data Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a durable, provenance-aware public-data foundation without changing the verified Phase 1 paper-trading authority.

**Architecture:** Extend the existing modular monolith with canonical provider protocols, validated point-in-time observations, and an evidence repository. Phase 2 owns public data collection and health; Strategy, Risk, Execution, Accounting, and live-trading prohibition remain unchanged.

**Tech Stack:** Python 3.12, asyncio, Pydantic/dataclasses, SQLAlchemy/Alembic, official `polymarket-client`, pytest, SQLite.

**Spec:** `docs/MASTER_SPEC.md`, `docs/intelligence/EVIDENCE.md`, and the user-supplied intelligence expansion update.

## Global Constraints

- Phase 1 behavior and P1-001–P1-030 must remain passing.
- Public data only; no wallet credentials, secure clients, or real orders.
- Exact `Decimal` for prices, quantities, liquidity, and timestamps in UTC.
- Evidence/provenance is descriptive and cannot authorize execution.
- Unknown, malformed, stale, or unversioned execution-critical data fails closed.
- Do not implement stock intelligence, macro providers, learning, or Phase 3 backtesting yet.

## Review Focus

- Duplicate snapshots must be idempotent by provider, source timestamp, and payload hash.
- Revised source data must create a new vintage rather than silently overwrite history.
- Missing or malformed timestamps/identifiers must be rejected before persistence.
- Stream disconnects and stale books must produce explicit health states and no new exposure.
- Evidence records must not expose vendor SDK objects or create an execution path.

### Task 1: Canonical evidence and provider contracts

**Files:** Create `backend/src/polytrader/evidence/models.py`, `backend/src/polytrader/providers/protocols.py`, and tests.

- [ ] Write failing tests for validated UTC source/collection timestamps, source metadata, revision, payload hash, market identity, and Decimal order-book observations.
- [ ] Implement immutable canonical models and provider protocols for market discovery, order books, and data-health status.
- [ ] Verify focused tests and Ruff/Pyright.

### Task 2: Evidence persistence and migration

**Files:** Modify `backend/src/polytrader/persistence/repository.py`; create Alembic migration and tests.

- [ ] Write failing tests for insert, idempotent duplicate, and distinct-vintage persistence.
- [ ] Implement SQLAlchemy evidence records with unique provenance keys and Decimal values stored losslessly.
- [ ] Add migration and verify upgrade plus persistence tests.

### Task 3: Polymarket snapshot ingestion

**Files:** Modify `backend/src/polytrader/integrations/polymarket/adapter.py`; create `backend/src/polytrader/market_data/ingestion.py` and tests.

- [ ] Write failing tests using a fake public source for market/token/order-book normalization and evidence creation.
- [ ] Implement a read-only ingestion service that records market and order-book snapshots with exchange and local timestamps.
- [ ] Verify with offline fakes, then run the separate real public smoke command.

### Task 4: Data health and safe API read model

**Files:** Create `backend/src/polytrader/market_data/health.py`; modify API read models and tests.

- [ ] Write failing tests for fresh, stale, disconnected, malformed, and recovered data-health states.
- [ ] Implement explicit health transitions and expose read-only `/api/v1/data-health` without changing order endpoints.
- [ ] Verify API tests and confirm no health state can approve an order.

### Task 5: Phase 2 validation and documentation

**Files:** Modify `scripts/verify.ps1`, `docs/STATE.yaml`, and this ExecPlan.

- [ ] Run Phase 1 quality gate, Phase 2 offline tests, public smoke, integration check, and clean startup/browser checks.
- [ ] Update STATE only with fresh evidence and record remaining Phase 2 work.
- [ ] Perform an adversarial review of provenance, point-in-time behavior, stale data, duplicate ingestion, and live-order impossibility.

## Definition of done

Canonical evidence, provenance, point-in-time snapshot persistence, provider contracts, Polymarket ingestion, and data-health read models are tested and verified. Phase 1 remains green and no new execution authority exists.
