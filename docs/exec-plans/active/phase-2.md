# Phase 2 ExecPlan — Data Foundation

## Objective

Implement the first data-foundation layer: provider contracts, validated point-in-time public Polymarket snapshots, evidence/provenance persistence, idempotent ingestion, and data-health states.

## Scope / non-goals

In scope: public Polymarket data, canonical evidence, timestamps, revisions, payload hashes, health, read-only API visibility, public market streaming, reconnects, order-book maintenance, and lifecycle events. Out of scope: stock providers, macro intelligence, feature engines, backtesting, learning, autonomous paper loops, MCP servers, wallets, secure clients, and live orders.

## Invariants

All Phase 1 invariants plus INV-019 through INV-025 apply. Evidence is not execution, historical data is point-in-time, and asset-specific execution boundaries remain intact.

## Architecture

`PolymarketPublicAdapter` → provider protocol → snapshot/stream validation → canonical `EvidenceObservation` / `MarketSnapshot` → SQLite repository → read-only API and health monitor. `ReconnectingMarketStream` → `OrderBookStore` maintains point-in-time books and lifecycle evidence. Existing Strategy → Risk → Paper Execution remains unchanged.

## Milestones

- P2-A provider/evidence models
- P2-B evidence persistence and migration
- P2-C Polymarket snapshot ingestion
- P2-D health and read-only API
- P2-E public streaming, reconnects, book maintenance, and lifecycle evidence
- P2-F validation and final review

## Validation commands

`backend/.venv/Scripts/python -m pytest backend/tests`, `powershell -ExecutionPolicy Bypass -File scripts/verify.ps1`, `powershell -ExecutionPolicy Bypass -File scripts/smoke_polymarket.ps1`, and `backend/.venv/Scripts/python scripts/check_research_integrations.py`.

## Progress

- Architecture and roadmap update: complete.
- P2-A through P2-E: complete and verified.
- P2-F: complete; full verification, public snapshot smoke, and public stream smoke passed.

## Definition of done

All P2 milestones have fresh evidence, Phase 1 remains complete and green, public snapshot and stream smokes pass, and no Phase 2 component can create or approve a real order. Phase 2 is COMPLETE; Phase 3 is the active next plan.
