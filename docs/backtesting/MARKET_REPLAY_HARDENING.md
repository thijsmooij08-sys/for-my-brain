# Market replay hardening

PolyTrader now incorporates useful research ideas from the external review
without importing third-party execution code.

## Added

- PolymarketFeeModel implements the price-sensitive V2 taker estimate
  notional times fee_rate times p times (1 - p), with maker exemption and
  exact Decimal arithmetic. ReplayFillModel accepts it as an optional mode;
  the existing flat-fee mode remains compatible.
- ResolutionSchedule records resolution, settlement, dispute status, and
  capital-lockup timing. It is metadata for simulation and accounting analysis,
  not a settlement authority.
- ConservativeQueueModel estimates resting-order fills only after modeled
  queue-ahead volume is consumed. It cannot submit or mutate an order.
- ReplayQualityAnalyzer reports duplicate sequence numbers, source-time
  regressions, and maximum collection lag instead of letting dataset sorting
  hide data defects.

## Boundaries

These features are simulation/research-only. They do not change the
Strategy -> RiskManager -> OrderIntent -> ExecutionEngine path, do not
authorize live execution, and do not load credentials. Full historical L2 queue
calibration still requires prospective PolyTrader captures or a separately
licensed dataset.

## Deliberately not imported

External full trading platforms, unified live clients, wallet code, and live
connectors remain excluded. Their useful patterns are represented by native,
tested PolyTrader value objects instead.
