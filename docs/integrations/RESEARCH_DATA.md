# Research data integrations

All integrations in this document are read-only research inputs. They produce
`EvidenceObservation` records and cannot create signals, orders, paper fills,
or live authority.

| Source | Adapter/package | Credentials | Status |
| --- | --- | --- | --- |
| Polymarket Data API v2 | `PolymarketDataApiV2Client` (`market_state`, `prices_history`) | None | Added and live-verified |
| SEC EDGAR/XBRL | `SecEdgarClient` | Local `POLYTRADER_SEC_USER_AGENT` only | Added |
| Nasdaq Data Link | `NasdaqDataLinkClient`, `nasdaq-data-link==1.0.4` | Optional local `NASDAQ_DATA_LINK_API_KEY` | Added in isolated environment |
| OpenBB | `openbb==5.0.0`, isolated descriptor | Provider-specific keys remain optional | Added in isolated environment |

SEC requests fail closed without an identifying User-Agent. Run
`powershell -ExecutionPolicy Bypass -File scripts/configure_sec_user_agent.ps1`
to write a locally controlled contact address to the ignored `.env` file; the
value is never displayed or committed. API keys are never stored in evidence,
logs, dashboards, or repository files. FRED/ALFRED was
removed from the active PolyTrader integration surface because this deployment
does not have an operator-owned key; it is not a runtime dependency or a
verified research source.

OpenBB is intentionally isolated because its current platform stack has newer
FastAPI/Pydantic requirements than the PolyTrader API. It is a research
workspace only and cannot become an execution dependency.

The official Data API v2 exposes public historical price series with
`/v2/prices-history` and `token_id`; a live request was verified against a
current public token. It does not provide a complete historical L2 order-book
archive, so PolyTrader persists its own timestamped book snapshots and stream
events for future replay. Historical price points must not be treated as
historical executable depth.
