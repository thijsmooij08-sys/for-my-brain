# Risk

RiskManager is deterministic and final. It checks the kill switch, stale data, spread, liquidity, configured order/market/total exposure limits, open position count, daily loss, and idempotency. It emits auditable APPROVED or REJECTED decisions with a reason code. Unknown critical data rejects opening exposure.

Future risk intelligence may add correlation, sector/geography/currency/rate/factor/event/shared-thesis exposure, scenario stress, and an `ExposureGraph`. These inform deterministic risk decisions but cannot replace hard limits. A future `CapitalPolicyEngine` allocates externally approved asset-class and strategy budgets above sizing; it cannot raise the global ceiling.

Shared intelligence must preserve asset-specific risk and execution boundaries.
Unknown provenance, stale point-in-time state, unresolved resolution rules, or
missing exposure data must fail closed for new exposure.
