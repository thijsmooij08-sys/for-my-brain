# Phase 7 ExecPlan — Shadow Forward Validation

## Objective

Evaluate current Champion and Challenger research outputs against live public Polymarket data in a shadow-only workflow. The workflow may scan, analyze, rank, size hypothetically, and record outcomes, but it must never submit, simulate as submitted, or authorize an order.

## Non-negotiable gates

- `LIVE_TRADING_ENABLED=false` remains authoritative.
- Shadow output is append-only evidence and is explicitly non-actionable.
- Current-data timestamps, provenance, freshness, and data-health checks are required.
- Champion/Challenger comparison uses forward evidence, not only historical replay.
- Existing Strategy → Signal → Opportunity → PositionSizer → RiskManager → OrderIntent → ExecutionEngine boundaries and Phase 1–6 invariants remain green.

## Milestones

- P7-A shadow data contract and no-order sink
- P7-B current-data forward evaluation and outcome journal
- P7-C Champion/Challenger comparison reports
- P7-D drift, freshness, and data-health reporting with fail-closed behavior
- P7-E complete Phase 1–6 regression and security gate

## Progress

- P7-A complete: `ShadowForecast`, freshness/provenance validation, append-only idempotent forward journal, and `ShadowOrderSink` rejecting every order intent are implemented and tested.
- P7-B complete: exact-Decimal scoring, current public-data collection, provenance, and delayed outcome settlement are implemented.
- P7-C complete: forward Champion/Challenger comparison reports are implemented as non-actionable artifacts.
- P7-D complete: absolute Brier-score drift reports, freshness/data-health gates, append-only persistence, and operational Grafana routing are implemented.
- P7-E complete: full regression, type, lint, build, public REST/stream, and live-execution safety gates passed.

## Delivery note

The operator dashboard was redesigned as a dark neon command center with API-backed paper accounting, current public market rows, explicit PAPER MODE/LIVE EXECUTION OFF controls, risk/data-health indicators, and a Grafana observability dashboard. The equity panel is intentionally a paper-accounting visual scaffold until a historical equity-series endpoint is exposed; it does not claim a return or trade performance.

## Verification

Each milestone requires focused tests, public REST/stream smoke checks, the complete verification suite, adversarial review, and freshly verified `docs/STATE.yaml` evidence. Do not begin Phase 8 work in this plan.
