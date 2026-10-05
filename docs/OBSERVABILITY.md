# PolyTrader observability

PolyTrader exposes Prometheus metrics from the API and provisions a local Grafana dashboard for paper-trading operations. These tools are diagnostic only; they cannot authorize an order or change the live-execution safety switch.

## Local endpoints

- Prometheus: `http://127.0.0.1:9090`
- Grafana: `http://127.0.0.1:3001`
- API metrics: `http://127.0.0.1:8000/metrics`
- API health: `http://127.0.0.1:8000/api/v1/health`
- Paper scorecard: `http://127.0.0.1:8000/api/v1/paper/performance`
- One bounded paper cycle: `POST http://127.0.0.1:8000/api/v1/paper/cycle?limit=20`

Docker also runs a restartable `paper-worker` service. It triggers the bounded
cycle every five minutes, records only simulated fills, and fails closed when
the API is unavailable or risk/data-health checks reject a market. Set
`PAPER_WORKER_ENABLED=false` when an operator wants a quiet stack.

The provisioned dashboard is **PolyTrader Overview** in the **PolyTrader** folder. It includes API request rate, API target health, the authoritative live-execution switch, and the active PAPER mode gauge. The dashboard is provisioned from `ops/grafana/provisioning/dashboards/polytrader-overview.json`.

Prometheus also loads `ops/prometheus/rules/polytrader.yml`. The rules alert
when the API is down, when the PAPER mode assertion disappears, or when the
live-execution gauge becomes non-zero. The last condition is an invariant
violation and must be treated as a stop-and-investigate event.

The same dashboard now includes paper equity, paper cash, fill count, closed-trade win rate, and a link to the live React paper dashboard. Win rate is shown as zero/no-sample until a paper sell closes a trade; no fictional success rate is generated.

## Safety semantics

`polytrader_live_execution_enabled` must remain `0`. `polytrader_trading_mode{mode="PAPER"}` must remain `1` for the local paper runtime. A green Grafana panel means the service is observable and in the expected safe mode; it does not mean that live trading is enabled.

## Verification

Run `scripts/verify.ps1` for the complete local quality gate. The public-data checks are `scripts/smoke_polymarket.ps1` and `scripts/smoke_polymarket_stream.ps1`.
