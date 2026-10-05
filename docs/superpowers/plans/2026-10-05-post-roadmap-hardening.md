# Post-roadmap hardening ExecPlan

## Objective

Strengthen the completed Phase 1–10 paper-only system using evidence-backed,
non-execution changes while preserving deterministic risk and every live-off
invariant.

## Status

- H1 state and documentation reconciliation: **COMPLETE**
- H2 supply-chain controls: **COMPLETE** (Dependabot configuration, local audit
  entrypoint, and fixed Vite 6.4.3 lockfile; remote GitHub Actions execution is
  not claimed)
- H3 operational safety alerts: **COMPLETE** (Prometheus rules loaded and
  verified through the local Prometheus API)
- H4 continuous public market capture: **COMPLETE** (Docker worker observed
  public snapshots and stream evidence in the shared ledger)
- H5 capture retention/backup and replay acceptance: **COMPLETE** (backup integrity, manifest retention, shared-ledger restore, and regression gates verified)
- H6 official stream-event completeness: **COMPLETE** (canonical evidence for
  `last_trade_price`, `tick_size_change`, and `best_bid_ask`; Decimal-safe
  serialization and repository tests verified)

## H4 design boundary

The capture service will use the existing read-only `PolymarketPublicAdapter`
and `StreamingIngestionService`, persist raw stream payload hashes and
canonical timestamped books, and expose only evidence/data-health outputs. It
must never import a secure client, accept a signer, or call an order endpoint.

## H5 acceptance gates

1. Restart-safe, append-only capture with duplicate-event idempotency.
2. Explicit source/received timestamps and payload hashes.
3. Bounded reconnect and stale-data health transitions.
4. Retention/backup policy tested against a disposable database.
5. Replay reconstructs the same book and paper-fill decisions.
6. Full regression and public read-only smokes pass with live execution still
   impossible.

No market-capture milestone may be reported complete until those checks have
actually run.

## H6 acceptance gates

1. Every currently documented public event that does not mutate a book has a
   typed canonical evidence path.
2. Event values preserve exact decimal text and source/collection timestamps.
3. Event evidence is append-only and provenance-hashed through the existing
   repository boundary.
4. The stream tests, complete verification suite, public-data smoke, and
   paper/live-off preflight all pass after the change.
