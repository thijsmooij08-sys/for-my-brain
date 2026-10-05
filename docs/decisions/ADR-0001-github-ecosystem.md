# ADR-0001: Approved GitHub ecosystem boundaries

## Decision

PolyTrader records every repository explicitly approved by the user in
`docs/integrations/GITHUB_ECOSYSTEM.md`. Research libraries are installed only
as an opt-in backend extra and are exposed through `polytrader.research`.

The canonical Phase 1 pipeline remains the sole owner of market state,
Decimal accounting, hard risk decisions, paper execution, and the live-order
deny path. Third-party libraries can produce analysis or observations only.

## Why

Several approved repositories are useful Python libraries, while others are
MCP servers, experiment platforms, reinforcement-learning frameworks, or an
archived equity backtester. Treating all of them as runtime dependencies would
expand credentials, network authority, and operational surface without making
the Phase 1 Polymarket workflow safer or more correct.

## Consequences

- Installed and tested: Alpaca SDK, pandas, Polars, scikit-learn, statsmodels,
  PyPortfolioOpt, Riskfolio-Lib, quantstats, VectorBT, Plotly compatibility
  pin, and Prometheus client.
- Reviewed but disabled: Alpaca MCP server, MLflow, FinRL, archived
  Quantopian Zipline, and SEC-EDGAR MCP. They remain future isolated research
  integrations and are not allowed to submit orders or access credentials.
- The exact versions and repository links are maintained in the ecosystem
  register; no third-party source is copied into the application.
