# Phase 8 live-readiness controls

Phase 8 defines the contracts needed to assess a future authenticated venue connection without creating one. `polytrader.live.readiness` contains no secure Polymarket SDK client, signer loader, credential store, wallet address, or network submission call.

## Controls

- `LiveSafetyConfig` rejects `LIVE_TRADING_ENABLED=true` and any non-`PAPER` mode.
- `AuthenticatedCapability` accepts only redacted metadata and rejects credential or signer references.
- `AccountSnapshot` uses `Decimal` values and requires source, revision, and UTC observation time.
- `UserStreamNormalizer` hashes non-secret event metadata; forbidden credential fields are rejected.
- `SequenceTracker` detects replay and sequence gaps; gaps make the stream unhealthy.
- `Reconciler` compares cash, equity, and positions exactly. Any mismatch is dirty.
- `EligibilityChecker` fails closed on disabled live mode, missing/stale account data, unhealthy streams, or dirty reconciliation.
- `CircuitBreaker` reports deterministic blocking reasons.
- `LiveExecutionStateMachine` is permanently `DISABLED` in this phase and its `submit` method raises `LiveTradingDisabledError`.

The `/api/v1/live-readiness` endpoint exposes only redacted diagnostics. It does not authenticate, connect a wallet, or authorize an order.

Phase 9 adds `GET /api/v1/live-preflight`, which reports policy, data-health,
eligibility, circuit-breaker, journal, and authorization checks without
accepting credentials. Its `activation_allowed` field is hard-coded false
while the repository safety policy is disabled.

Phase 9 also includes a redacted reconciliation rehearsal path. It uses the
same exact-`Decimal` `Reconciler` as readiness checks and deliberately proves
that cash, equity, position, or account identity mismatches become dirty.
