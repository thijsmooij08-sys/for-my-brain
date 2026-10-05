# Intelligence and evidence architecture

This is the bounded Phase 4 research plane. It is not an execution authority.

## Boundaries

```text
sources → observations → claims/forecasts → features → intelligence → asset strategy
```

Planned module families are fundamentals, valuation, competitive/peer, earnings, dividends/income, technical, macro, events, and quantitative patterns. Feature families are technical, fundamental, event, macro, and market microstructure. Evidence storage is organized as sources, observations, claims, forecasts, and provenance.

Potential future engines include `StockDiscoveryEngine`, `ValuationEngine` (bear/base/bull scenarios with assumptions/sensitivity), `PeerIntelligenceEngine`, `EarningsIntelligenceEngine`, `EventStudyEngine`, `MacroRegimeEngine`, `IncomeFactorEngine`, `PatternDiscoveryEngine`, `CapitalPolicyEngine`, `ExposureGraph`, `ScenarioEngine`, and `SignalFusionEngine`.

Every observation records source, source timestamp, collection timestamp, value, revision/vintage, and model version. Qualitative conclusions require supporting evidence. Consensus values must come from structured reliable sources, never invented by an LLM. Historical features must be point-in-time correct.

Pattern search retains hypothesis, sample, effect size, uncertainty interval, training/validation/out-of-sample results, costs, and final net result. Require holdouts or walk-forward evaluation, minimum samples, stability checks, bootstrap intervals, and multiple-comparison/false-discovery controls where appropriate. No intelligence component is a strategy or capital authorization by itself.

The implemented `polytrader.intelligence` modules produce research-only outputs with evidence, timestamps, model versions, confidence, disagreement, and limitations. Stock and Polymarket strategies may consume shared evidence, but remain independent implementations with separate opportunities, sizing, risk, and execution. Model disagreement is retained as a feature and shown to reviewers.
