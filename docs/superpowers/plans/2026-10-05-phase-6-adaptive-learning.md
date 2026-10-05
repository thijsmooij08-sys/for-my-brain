# Phase 6 ExecPlan — Controlled Adaptive Learning

## Objective

Add research-only learning infrastructure that attributes paper outcomes, calibrates probabilities, and evaluates experiments without bypassing Strategy, Opportunity, PositionSizer, RiskManager, ExecutionEngine, Accounting, or the permanent live-trading prohibition.

## Scope and gates

- Learning consumes immutable, point-in-time paper/replay evidence and produces versioned research artifacts.
- Every artifact records dataset, feature, strategy, and code provenance plus evaluation timestamps.
- Calibration, attribution, ablation, counterfactual, and Champion/Challenger outputs remain non-actionable until deterministic policy and risk approve any later paper allocation.
- Learning cannot raise capital limits, weaken loss limits, disable circuit breakers, bypass eligibility, or grant live authority.
- No Phase 7 shadow execution or Phase 8 authenticated/live-capable integration work begins in this phase.

## Milestones

- P6-A immutable trade attribution and outcome ledger
- P6-B probability calibration and reliability metrics
- P6-C experiment, dataset, model, and strategy registries
- P6-D feature ablation and counterfactual evaluation
- P6-E Champion/Challenger comparison, promotion/rollback policy, and Phase 1–5 regression gate

## Progress

- P6-A complete: immutable Decimal round-trip attribution ledger with dataset/evidence provenance and append-only idempotent persistence.
- P6-B complete: exact Decimal Brier score and expected calibration error with invalid-input rejection.
- P6-C complete: content-addressed immutable registry for model, dataset, and strategy artifacts; all entries remain non-actionable.
- P6-D complete: feature-ablation and counterfactual evaluators emit exact-Decimal, provenance-bearing, non-actionable research artifacts.
- P6-E complete: Champion/Challenger minimum-evidence and improvement gates, append-only promotion/rollback records, and deterministic Phase 1–5 protections are implemented.

## Verification

Each milestone requires focused tests, the complete backend/frontend verification suite, public-data smoke checks where applicable, documentation updates, and freshly verified `docs/STATE.yaml` evidence before the phase can be marked complete.

## Verified result

COMPLETE on 2026-10-04 UTC. The full backend suite passed (64 tests), Ruff and Pyright passed, frontend build passed, public Polymarket REST and streaming smoke checks passed, research integrations passed for DuckDB/Pandera/Hypothesis/Apache Arrow/OpenTelemetry, and Docker API/Prometheus/Grafana health checks passed. Learning remains research-only and cannot place or authorize orders.
