# Learning system (research-only)

Phase 6 implements controlled research artifacts for experiment → backtest → validation → out-of-sample → shadow → paper evaluation. Attribution, calibration, registries, ablation, counterfactuals, Champion/Challenger comparison, and append-only rollback records are available, but every artifact is non-actionable. Learning may recommend within configured limits but cannot increase global risk.

Future learning may evaluate which evidence/features contribute to a validated strategy. It must preserve source vintages, feature versions, hypothesis samples, uncertainty, multiple-hypothesis controls, and component disagreement; it may not convert a research observation directly into an order.

Future attribution should cover feature, strategy, model, factor, event type,
regime, asset class, and market category. Feature ablation, calibration,
counterfactuals, champion/challenger comparison, rollback, and capital-policy
budgets are validation stages, not autonomous authority.

Phase 7 consumes these artifacts in the shadow plane. Forward reports require
fresh public-data evidence and remain append-only. A shadow report cannot create
an `OrderIntent`; the terminal `ShadowOrderSink` rejects every intent. No
learning output can bypass `RiskManager`, change hard limits, disable a
circuit-breaker, or grant live execution authority.
