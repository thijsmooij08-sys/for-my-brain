# Architecture

PolyTrader is a Python/FastAPI modular monolith with a React dashboard. The Polymarket SDK stays behind `integrations/polymarket`; SDK models never escape into business modules.

`market_data` normalizes external facts. `strategies` emits non-authoritative Signals. `opportunities` turns Signals into explainable candidate actions. `sizing` proposes exposure. `risk` is the deterministic authority. `execution` creates paper-only, book-walked fills. `portfolio` owns positions, cash, and P&L. `persistence` records auditable state. `api` exposes read models, not ORM models.

There is no live execution adapter. A deliberate `LiveTradingDisabledError` is the only future-facing boundary, and `ShadowOrderSink` rejects every order intent while preserving a testable no-order path.

## Future intelligence plane

Future multi-asset intelligence is a research/evidence plane upstream of strategies, never an execution authority:

```text
data providers → evidence/provenance → features → intelligence modules
                                      ↓
                         signal fusion / research outputs
                                      ↓
                  asset-specific Strategy → Opportunity → Sizing → Risk
```

Planned bounded modules include `intelligence/fundamentals`, `valuation`, `competitive`, `earnings`, `dividends`, `technical`, `macro`, `events`, and `patterns`, with corresponding feature namespaces. `evidence/sources`, `observations`, `claims`, `forecasts`, and `provenance` preserve source and revision timestamps.

Future concepts include `FeatureObservation`, `EvidenceSource`, `EvidenceClaim`, `Forecast`, `ValuationScenario`, `EventStudy`, `MacroRegime`, `DiscoveryScorecard`, `ExposureGraph`, `StressScenario`, `CapitalPolicy`, and `FusedSignal`. None is implemented or authoritative in Phase 1. Stocks and Polymarket may share evidence/features, but retain independent strategies, risk decisions, and execution adapters.

## Target multi-asset architecture

Phase 2 begins the data foundation only. The target shape is:

```text
Stock / Polymarket / Macro providers
              ↓
      validation + canonical models
              ↓
   point-in-time evidence + provenance
              ↓
 technical / fundamental / event features
              ↓
        intelligence + signal fusion
              ↓
 asset-specific strategy → opportunity → sizing → deterministic risk
              ↓
 asset-specific execution → positions → accounting → review → learning
```

Provider abstractions (`MarketDataProvider`, `FundamentalDataProvider`,
`MacroDataProvider`, `NewsProvider`, `FilingsProvider`, `OptionsDataProvider`,
`EventDataProvider`, and `ResearchDataProvider`) return canonical PolyTrader
models. Vendor SDK objects never cross the integration boundary. Stocks and
Polymarket share evidence and portfolio intelligence only; their market
mechanics, fee models, risk rules, and execution adapters remain separate.

Phase 4 implements the initial research-only subset in `polytrader.intelligence`: technical features, event studies, valuation scenarios, fundamentals/peer/earnings/macro/income adapters, pattern reports, signal fusion, and a Polymarket event graph. These outputs remain non-actionable and cannot authorize capital.

Future intelligence modules are explicitly bounded: `StockDiscoveryEngine`,
`FundamentalIntelligenceEngine`, `ValuationEngine`, `PeerIntelligenceEngine`,
`EarningsIntelligenceEngine`, `TechnicalFeatureEngine`, `EventStudyEngine`,
`PatternDiscoveryEngine`, `MacroRegimeEngine`, `IncomeFactorEngine`,
`MarketEventGraph`, `ExposureGraph`, `ScenarioEngine`, `CapitalPolicyEngine`,
and `SignalFusionEngine`. Later engines remain non-authoritative until separately validated.

## Shadow validation plane

Phase 7 adds `services/shadow.py` as a forward-evidence plane after learning and
before any future live-readiness work. `ShadowForecast` requires source and
dataset provenance, point-in-time timestamps, and an artifact hash. Freshness
is checked through `DataHealthMonitor`; stale, future, or disconnected evidence
fails closed. `ShadowForwardEvaluator` produces exact-Decimal Brier reports and
`ShadowForwardJournal` stores append-only, idempotent records. Reports are
always `actionable=False`. `ShadowOrderSink` never submits or simulates an
order, even if passed an otherwise valid `OrderIntent`.
