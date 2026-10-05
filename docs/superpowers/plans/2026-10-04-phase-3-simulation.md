# Phase 3 ExecPlan — Simulation and Replay

## Objective

Build a trustworthy research simulator around the verified Phase 2 evidence stream: point-in-time dataset manifests, historical replay, realistic book-walking paper fills, fees, slippage, latency, and backtest metrics.

## Narrow focus

The first paper-trading research loop will focus on liquid, actively updating Polymarket binary markets with complete yes-token books. Stock, macro, and multi-asset intelligence remain adapters and schemas only until this core produces reproducible evidence.

## Non-goals

No autonomous trader, adaptive learning, authenticated clients, wallet handling, real orders, or live execution.

## Development target

Local Docker Compose is the default reproducible target. The API and dashboard run as separate services with a named SQLite volume, paper mode, and `LIVE_TRADING_ENABLED=false` explicitly set.

## Milestones

- P3-A dataset manifest and immutable replay inputs
- P3-B event replay clock and deterministic ordering
- P3-C realistic fills, fee/slippage/latency models
- P3-D backtest metrics and artifact persistence
- P3-E point-in-time feature access, scenario shocks, and multiple-hypothesis protection
- P3-F adversarial verification and Phase 1/2 regression checks

## Acceptance gate

Every simulation result must identify its dataset version, source timestamps, strategy version, fill model, latency model, and software version; results must be deterministic and must not change risk or execution authority.

## Progress

P3-A through P3-F are complete. Forty backend tests pass, including deterministic replay, exact-decimal fills, scenario handling, point-in-time feature access, and Benjamini–Hochberg discovery control. Full repository verification and public-data smokes remain the final gate.
