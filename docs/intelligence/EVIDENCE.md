# Evidence and point-in-time data

Evidence is the durable bridge between external data and future intelligence.
It is not a strategy and cannot authorize capital.

## Canonical observation fields

Every material observation should preserve:

- `source` and `source_type`
- source URL/reference where appropriate
- `source_timestamp` and `collected_at` in UTC
- value and canonical unit
- revision/vintage identifier
- market, ticker, event, or token relationship
- confidence and validation status
- feature/model/strategy versions that consumed it

Raw provider payloads remain separate from derived features and claims. A
historical query must select the latest observation known at the decision time,
not the latest value today. Revisions are new vintages, never silent rewrites.

## Phase 2 scope

Phase 2 implements canonical evidence records for public Polymarket snapshots,
including market identity, resolution metadata when available, order-book
levels, exchange timestamp, local ingest timestamp, provider, and payload hash.
It also defines provider protocols and data-health states. Stock, macro, news,
filings, and options providers remain interfaces or later-phase adapters.

## Safety

Evidence can inform features and research reports. It cannot bypass the
Strategy → Opportunity → Sizing → Risk → Execution boundary. Unknown,
malformed, stale, or unversioned execution-critical data fails closed.
