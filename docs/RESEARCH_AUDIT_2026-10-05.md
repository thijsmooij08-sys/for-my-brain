# PolyTrader post-roadmap research audit

Date: 2026-10-05 UTC

## Executive result

The Phase 1–10 architecture is complete and remains paper-only. The audit did
not find a trustworthy third-party Polymarket bot that should be copied into
the execution path. Public bot repositories are often unlicensed, strategy-
specific, or expose live-wallet code; they are useful only as research
references after manual review.

The remaining work is operational hardening, not a new trading authority:

1. continuously retain raw Polymarket market-stream events and periodic books
   for future executable-depth replay;
2. add dependency and GitHub supply-chain checks; and
3. add fail-closed operational alerts for API loss, loss of PAPER mode, and
   any non-zero live-execution metric.

The follow-up audit also compared the capture path with the current official
[real-time market-data event reference](https://docs.polymarket.com/market-data/realtime-data).
The stream documents `book`, `price_change`, `last_trade_price`,
`tick_size_change`, `best_bid_ask`, `new_market`, and `market_resolved`.
PolyTrader now persists canonical, timestamped evidence for the three
non-book quote/trade events as well, without allowing them to mutate a book or
grant any execution authority.

The read-only `market-capture` Docker worker has now been added and verified.
It persisted initial snapshots plus public streaming book evidence into the
existing append-only repository, with restart-safe duplicate handling. A
shared-ledger check observed 149 evidence records, including 129 stream
records, during the verification window.

The `backup-worker` now creates online SQLite backups into a Docker volume,
hashes each file, verifies `PRAGMA integrity_check`, and retains a bounded
manifest (24 backups by default). A live backup was opened successfully and
contained 777 evidence rows during verification.

During the audit, npm audit identified the vulnerable Vite 6.0.5/esbuild
chain. Vite was upgraded to the compatible fixed 6.4.3 release, the lockfile
was regenerated, the frontend build passed, and a full npm audit returned zero
vulnerabilities.

The same scan then found vulnerable Starlette 0.41.3 in the pinned FastAPI
stack. FastAPI was upgraded to 0.142.2 with Starlette 1.7.0, the security
extra now pins `pip-audit==2.10.1`, and the Python audit reports no known
vulnerabilities.

## Sources checked

- [Official Polymarket Python SDK](https://github.com/Polymarket/py-sdk) and
  its [current changelog](https://github.com/Polymarket/py-sdk/blob/main/CHANGELOG.md).
  The installed `polymarket-client` is 0.12.0, the current PyPI release. The
  SDK's recent changes reinforce Data API v2 reads, typed stream/order-book
  models, and bounded reconnect behavior; the existing public adapter remains
  the correct boundary.
- [Polymarket Data API v2](https://data-api.polymarket.com/v2/docs): public
  market state, activity, portfolio, and price-history data. It does not
  replace prospective capture of full executable L2 depth.
- [GitHub dependency review](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review),
  [PyPA pip-audit](https://github.com/pypa/pip-audit), and the
  [OpenSSF Scorecard action](https://github.com/ossf/scorecard-action): free
  supply-chain controls suitable for this repository.
- [Prometheus alerting rules](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
  and [Grafana alert provisioning](https://grafana.com/docs/grafana/latest/alerting/set-up/provision-alerting-resources/file-provisioning/):
  deterministic, repository-owned operational alerts.
- [Polymarket real-time market data](https://docs.polymarket.com/market-data/realtime-data):
  authoritative public stream event types and typed payload fields used by the
  capture completeness check.
- [GitHub artifact attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations):
  recommended for a future configured remote, but not enabled locally because
  this checkout has no verified GitHub Actions execution context.

## GitHub review decisions

### Adopt as controlled infrastructure

- Dependabot configuration for Python, npm, Docker, and GitHub Actions.
- CI checks for the existing verification suite plus dependency audit and
  secret scanning. These checks report findings; they never grant execution
  authority.
- OpenSSF Scorecard when this repository has a GitHub remote and Actions are
  enabled. The workflow must use least-privilege permissions and pinned action
  versions before activation.

### Keep as research-only references

The Polymarket bot repositories returned by GitHub search were not adopted:
their licenses, data provenance, and live-wallet boundaries were inconsistent.
Order-book simulators may inform isolated benchmark experiments, but the
native Decimal book-walking simulator remains authoritative.

### Do not add

- secure Polymarket clients, wallet/signing packages, or trading MCP servers;
- archived Zipline/FinRL as runtime dependencies;
- an LLM or third-party bot as a RiskManager or execution authority;
- any provider key or account credential in the repository or chat.

## Required follow-up backlog

The active hardening goal tracks these items as separate, verifiable tasks.
They must not be used to change `LIVE_TRADING_ENABLED=false`, bypass
RiskManager, or mark a paper result profitable without sufficient closed-trade
evidence.
