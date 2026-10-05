# Phase 9 ExecPlan — Limited-Live Preparation (Activation Disabled)

## Objective

Prepare production-like controls for a future limited-live deployment without
placing or enabling real orders. This phase adds explicit authorization and
operational gates around the already fail-closed Phase 8 boundary.

## Non-negotiable gates

- `LIVE_TRADING_ENABLED=false` remains authoritative.
- No private key, signer, credential, wallet connection, or authenticated order
  submission is loaded or requested.
- Every activation request is denied while the repository policy is disabled.
- RiskManager, eligibility, reconciliation, and circuit breakers remain
  mandatory and cannot be bypassed by a future adapter or learning system.
- Phases 1–8 remain green.

## Milestones

- P9-A explicit authorization and policy gate contracts
- P9-B production-like preflight and operational checklist
- P9-C account/reconciliation rehearsal using redacted fixtures
- P9-D API/observability exposure for gate decisions
- P9-E adversarial regression and documentation audit

## Scope exclusions

No real order submission, wallet authentication, signer loading, live activation,
or Phase 10 adaptive-live work is allowed in this plan.

## Verification

Focused unit tests, full regression, public-data smoke tests, Docker health,
secret scan, and a manual audit proving every activation path remains denied.

## Progress

- P9-A complete: `ActivationRequest`, `ActivationDecision`, and `LimitedLiveGate`
  provide an auditable operator-intent contract while always returning denied
  under the repository policy. No credential, signer, wallet, or venue client
  is accepted.
- P9-B complete: deterministic operational preflight checks cover policy lock,
  paper mode, data health, account eligibility, circuit breakers, journal
  integrity, and authorization.
- P9-D complete: redacted `GET /api/v1/live-preflight` exposes those checks and
  always reports `activation_allowed=false`.
- P9-C complete: `RehearsalFixture` and `run_reconciliation_rehearsal` exercise
  exact-Decimal clean and mismatch account reconciliation using redacted data.
- P9-E pending: final adversarial regression and documentation audit.
