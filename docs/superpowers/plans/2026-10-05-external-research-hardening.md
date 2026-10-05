# External Research Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add safe, provenance-aware research boundaries inspired by approved external projects without importing live-trading authority or third-party execution code.

**Architecture:** A typed catalog records external projects and the exact research-only patterns accepted from each. A dependency-free JSONL importer converts pre-reviewed external snapshots into PolyTrader's existing `ReplayDataset` contract, preserving timestamps, hashes, and deterministic ordering. Documentation records rejected projects and licensing/security decisions.

**Tech Stack:** Python 3.11+, existing `ReplayDataset`, JSONL, SHA-256, pytest, Ruff, Pyright.

**Spec:** `AGENTS.md`, `docs/INVARIANTS.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`.

## Global Constraints

- Exact `Decimal` values remain authoritative for prices, quantities, fees, and P&L.
- Imported research data can never create an `OrderIntent` or call an execution client.
- No wallet credentials, signers, private keys, or live-order endpoints are added.
- External source code is not copied into the runtime; only reviewed schemas and research patterns are adopted.
- Every imported dataset is content-addressed and retains source/license/provenance metadata.

## Review Focus

- Malformed or time-travel JSONL events must fail closed.
- External data must not silently become executable trading authority.
- Duplicate sequence numbers and invalid hashes must be rejected.
- Decimal strings must remain exact rather than becoming binary floats.
- Unknown catalog source IDs must not be treated as approved.

---

### Task 1: External research decision catalog

**Files:**
- Create: `backend/src/polytrader/research/external_catalog.py`
- Test: `backend/tests/test_external_research.py`
- Create: `docs/integrations/EXTERNAL_RESEARCH_REVIEW_2026-10-05.md`

- [x] Write failing tests for approved research-only sources, rejected live-capable sources, and unknown-source rejection.
- [x] Implement immutable catalog entries with source URL, evidence boundary, license status, and execution prohibition.
- [x] Document extracted lessons from OpenMarket, oraclebook, hftbacktest, polymarket-backtest, order-book-sim, PolyBench, PredictionMarketBench, alpha-lake, PMXT, and the rejected live-capable projects.
- [x] Run focused tests and the full backend suite.

### Task 2: Provenance-preserving external replay importer

**Files:**
- Create: `backend/src/polytrader/research/external_replay.py`
- Modify: `backend/src/polytrader/research/__init__.py`
- Test: `backend/tests/test_external_research.py`

- [x] Write failing tests for canonical JSONL import, exact Decimal payload preservation, source/license metadata, malformed input, duplicate sequences, and timestamp regression.
- [x] Implement a dependency-free importer that accepts only canonical `ReplayEvent` JSONL and returns the existing `ReplayDataset` plus an external source manifest.
- [x] Ensure the importer is read-only, never imports arbitrary modules, and never exposes an execution method.
- [x] Run focused tests and the full backend suite.

### Task 3: Verification and state reconciliation

**Files:**
- Modify: `docs/INDEX.md`
- Modify: `docs/STATE.yaml`
- Modify: `docs/integrations/GITHUB_ECOSYSTEM.md`

- [x] Add the external research review to the documentation index and ecosystem register.
- [x] Run Ruff, Pyright, `scripts/verify.ps1`, public-data smoke, research integration checks, and Compose validation.
- [x] Confirm `LIVE_TRADING_ENABLED=false`, Docker paper mode, and no signer/credential paths.
- [x] Update `docs/STATE.yaml` only with freshly verified evidence.
- [x] Commit and publish the changes.

### Task 4: Vibe-inspired research artifacts

**Files:**
- Create: `backend/src/polytrader/research/debate.py`
- Modify: `backend/src/polytrader/services/review.py`
- Modify: `backend/src/polytrader/research/__init__.py`
- Test: `backend/tests/test_vibe_research.py`
- Modify: `docs/integrations/EXTERNAL_RESEARCH_REVIEW_2026-10-05.md`

- [x] Add deterministic multi-agent debate artifacts with evidence IDs, exact confidence, provenance, and `actionable=false`.
- [x] Add Decimal paper-journal summaries for cycle, eligibility, buy, and sell counts.
- [x] Reuse the existing shadow-forward evaluator for shadow backtesting; do not duplicate execution or add live connectors.
- [x] Run the focused tests and complete verification suite.
