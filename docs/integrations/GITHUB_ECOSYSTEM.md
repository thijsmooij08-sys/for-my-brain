# GitHub ecosystem review

Last checked: 2026-10-04. The approved repositories have been inventoried and assigned an explicit integration boundary. “Added” means either installed as an optional, tested dependency or represented by a reviewed adapter/configuration boundary; it does not mean copying third-party source into PolyTrader.

| Repository | Ownership / license | Maintenance & security assessment | Decision | Phase 1 rationale |
| --- | --- | --- | --- | --- |
| [Polymarket/py-sdk](https://github.com/Polymarket/py-sdk) | Official, MIT | Active release `polymarket-client` 0.12.0; typed public/secure clients; standard lockfile/tests | ADD | Official read-only public market and book adapter only; pin and isolate behind adapter. |
| [alpacahq/alpaca-py](https://github.com/alpacahq/alpaca-py) | Official, Apache-2.0 | Official market-data SDK; trading APIs also exist | ADDED (research extra) | Installed 0.44.0; future read-only data adapter only, never a PolyTrader execution authority. |
| [alpacahq/alpaca-mcp-server](https://github.com/alpacahq/alpaca-mcp-server) | Official, MIT | MCP server includes trading operations and credential configuration | REVIEWED / NOT ENABLED | Added to this decision register only. No server, credentials, or MCP tools are configured in Phase 1. |
| [pydata/pandas](https://github.com/pandas-dev/pandas) | Official, BSD-3-Clause | DataFrame/time-series foundation | ADDED (research extra) | Installed 2.3.3 behind research adapters. |
| [pola-rs/polars](https://github.com/pola-rs/polars) | Official, MIT | Fast tabular research data | ADDED (research extra) | Installed 1.44.2; no accounting ownership. |
| [scikit-learn/scikit-learn](https://github.com/scikit-learn/scikit-learn) | Official, BSD-3-Clause | Future feature/model research | ADDED (research extra) | Installed 1.9.1; no model may approve orders. |
| [statsmodels/statsmodels](https://github.com/statsmodels/statsmodels) | Official, BSD-3-Clause | Statistical research | ADDED (research extra) | Installed 0.15.0; advisory only. |
| [robertmartin8/PyPortfolioOpt](https://github.com/robertmartin8/PyPortfolioOpt) | Community, MIT | Portfolio research/optimization | ADDED (research extra) | Installed 1.6.0; wrapped as Decimal-returning suggestions only. |
| [polakowo/vectorbt](https://github.com/polakowo/vectorbt) | Community, Apache-2.0 | Research/backtest library | ADDED (research extra) | Installed 0.28.5 with Plotly 5.24.1 compatibility pin; cannot own accounting. |
| [dcajasn/Riskfolio-Lib](https://github.com/dcajasn/Riskfolio-Lib) | Community, BSD-3-Clause | Portfolio research/optimization | ADDED (research extra) | Installed 7.4.0; future research only; hard risk remains native. |
| [ranaroussi/quantstats](https://github.com/ranaroussi/quantstats) | Community, Apache-2.0 | Performance analytics | ADDED (research extra) | Installed 0.0.86 behind a paper-history summary adapter. |
| [prometheus/client_python](https://github.com/prometheus/client_python) | Official Prometheus, Apache-2.0 | Monitoring client | ADDED (core runtime) | Installed 0.24.1 for compatibility with Feast; API metrics only, no authority changes. |
| [mlflow/mlflow](https://github.com/mlflow/mlflow) | Official project, Apache-2.0 | Experiment tracking and model/artifact registry | ADDED (research extra) | Installed 3.16.1; local tracking only, no model or execution authority. |
| [optuna/optuna](https://github.com/optuna/optuna) | Official project, MIT | Controlled hyperparameter and strategy-parameter experiments | ADDED (research extra) | Installed 5.0.0; study suggestions remain research-only. |
| [PrefectHQ/prefect](https://github.com/PrefectHQ/prefect) | Official project, Apache-2.0 | Local workflow orchestration | ADDED (research extra) | Installed 3.8.7; no scheduler/server is started by PolyTrader. |
| [feast-dev/feast](https://github.com/feast-dev/feast) | Official project, Apache-2.0 | Point-in-time feature registry and offline/online feature boundary | ADDED (research extra) | Installed 0.66.0; no feature store is authoritative for risk or execution. |
| [nautechsystems/nautilus_trader](https://github.com/nautechsystems/nautilus_trader) | Official project, LGPL-3.0 | Sophisticated multi-venue architecture | REJECT FOR PHASE 1 | Would duplicate execution, positions, portfolio, risk, and simulation ownership. Patterns may inform later review. |
| [mlflow/mlflow](https://github.com/mlflow/mlflow) | Official project, Apache-2.0 | Experiment tracking platform and service | REVIEWED / DEFERRED | Requires a tracking backend and expands operations; reserved for a later research phase. |
| [quantopian/zipline](https://github.com/quantopian/zipline) | Archived, Apache-2.0 | Historical US-equity backtester | REVIEWED / NOT INSTALLED | Repository is archived and not a Polymarket/Phase 1 runtime dependency; use a future isolated evaluation only. |
| [AI4Finance-Foundation/FinRL](https://github.com/AI4Finance-Foundation/FinRL) | Community, Apache-2.0 | RL research framework | REVIEWED / DEFERRED | Large research surface and training dependencies; cannot influence Phase 1 execution. |
| [stefanoamorelli/sec-edgar-mcp](https://github.com/stefanoamorelli/sec-edgar-mcp) | Community, verify before use | SEC research MCP candidate | REVIEWED / NOT ENABLED | Requires a separately governed MCP/data boundary; no credentials or external server enabled. |

Supply-chain decision: adopt only packages from official registries, pin direct versions, generate lockfiles, review license/requirements, and do not execute third-party install scripts. No installed Phase 1 addition requires secrets or has independent trade authority. Major additions receive an ADR in `docs/decisions/`.

Installed research/runtime additions (verified 2026-10-04): `duckdb==1.5.6`, `pyarrow==25.0.1`, `opentelemetry-api==1.45.0`, `opentelemetry-sdk==1.45.0`, `prometheus-client==0.24.1`, `pandera==0.33.1`, `hypothesis==6.168.3`, `mlflow==3.16.1`, `optuna==5.0.0`, `prefect==3.8.7`, and `feast==0.66.0`. Grafana is provisioned locally as `grafana/grafana:13.2.3` with Prometheus `prom/prometheus:v3.8.0`; the dashboard is exposed on `http://127.0.0.1:3001` because host port 3000 is occupied. These additions are infrastructure/research-only and cannot authorize orders or override RiskManager.

## Repository controls added 2026-10-05

The linked repository now has repository-owned definitions for:

- pull-request CI covering backend tests, Ruff, Pyright, Alembic, pip-audit,
  frontend build, secret scan, and Compose validation;
- CodeQL for Python and JavaScript/TypeScript;
- dependency review with high-severity and prohibited-license gates;
- OpenSSF Scorecard with SARIF upload;
- Hadolint and Trivy Docker checks;
- source-artifact upload and GitHub build-provenance attestation;
- CODEOWNERS, pull-request and issue templates, security policy, and
  contribution rules.

All external Actions are pinned to immutable commit SHAs. Workflows have no
wallet credentials, signer inputs, or live-order permissions. Branch
protection requiring CI and owner review must be enabled in GitHub repository
settings after the first push; workflow files cannot safely enable that
repository setting by themselves.

The 2026-10-05 external-project scan is recorded in
`EXTERNAL_RESEARCH_REVIEW_2026-10-05.md`. Only research patterns from reviewed
projects are adopted; live-capable trading agents remain rejected from the
PolyTrader runtime.
