# Exposure graph and capital policy (future)

The future portfolio layer will map positions and opportunities to shared risk
drivers such as company, sector, country, currency, rates, inflation, growth,
political candidate, election, policy, event, and thesis.

An `ExposureGraph` may identify hidden concentration when many small positions
share one driver. A `ScenarioEngine` may estimate shocks such as rates +200 bp,
equities -20%, USD +15%, oil +50%, credit widening, recession, inflation, or
Polymarket event changes.

The `CapitalPolicyEngine` sits above strategy allocation:

```text
total approved capital → asset-class budget → strategy budget → sizing → risk
```

Budgets are externally configured. Learning can allocate within them but cannot
raise the global or asset-class ceiling. Analytical exposure and scenario
outputs inform deterministic risk; they never replace hard limits.

No exposure graph, scenario engine, or capital-policy runtime is implemented in
Phase 2 unless its own ExecPlan and tests are approved by the roadmap.
