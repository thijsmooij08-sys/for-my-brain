# External research review — 2026-10-05

This review records the useful ideas extracted from the approved external-project
scan. PolyTrader does not copy third-party trading agents, secure clients, wallet
code, or live-order paths. The catalog in
`backend/src/polytrader/research/external_catalog.py` is the executable boundary.

## Adopted research patterns

| Source | Extracted pattern | PolyTrader boundary |
| --- | --- | --- |
| OpenMarket | timestamp-locked paired-market replay and honest null-result reporting | research dataset only; no strategy promotion by itself |
| oraclebook | event bus, composable gates, and recorded-order-flow replay | compare with existing pipeline; RiskManager remains native |
| hftbacktest | queue position, latency, and L2/L3 microstructure evaluation | isolated simulator tests only |
| polymarket-backtest | V2 fee model, no-lookahead replay, and performance statistics | compare against existing Decimal fill model |
| order-book-sim | deterministic matching-engine and event-log test ideas | test fixtures only |
| PolyBench | timestamp-locked LLM forecast evaluation | benchmark-only, never an order signal |
| PredictionMarketBench | agent evaluation over historical LOB/trade replay | benchmark-only, never an execution authority |
| alpha-lake | bitemporal facts and provenance-aware data lake concepts | schema review only; existing evidence store remains authoritative |
| PMXT | venue-normalization concepts | no trading endpoints or unified execution client |
| Marketlens | historical L2, queue-aware replay, and latency evidence | provider/license review required before data import |
| Polymarket Trader | modular adapter and paper-fill comparison ideas | comparison only; no duplicate runtime |
| NautilusTrader | deterministic event clocks, adapter boundaries, and high-resolution replay | isolated reference only; no Rust engine or live adapter in the runtime |
| Hummingbot | order-book tracker, user-stream supervision, and connector lifecycle patterns | extract interface ideas only; no key stores, gateway, or order connectors |
| Freqtrade | dry-run lifecycle, look-ahead/recursive analysis, and performance reporting | testing concepts only; crypto strategy runtime is out of scope |
| Kronos | OHLCV tokenizer/forecast interface and challenger-model evaluation | optional research model only; never a Polymarket order signal |

## Explicitly rejected for the runtime

Homerun, OpenPoly, NewWorldTrading, and Vibe-Trading include live-capable or
agent-driven trading surfaces. Their source may be read for threat modeling and
architecture comparison, but it is not installed, imported, or connected to
PolyTrader.

## Import boundary

External snapshots may only enter through the canonical JSONL replay importer.
Each event must already contain source and collection timestamps, a payload hash,
unique sequence, token identity, and canonical payload values. The importer
creates a content-addressed `ReplayDataset`; it cannot create an order intent,
load credentials, or call a venue.

No external dataset has been downloaded into the repository by this review. Any
future dataset addition must pass license, provenance, reproducibility, and
look-ahead-bias review first.

## Vibe-inspired concepts added safely

The following concepts were implemented without importing Vibe-Trading:

- `ResearchDebate` records deterministic multi-agent positions, evidence IDs,
  confidence, disagreement, and dataset provenance. It is explicitly
  non-actionable.
- `TradeJournalAnalyzer` summarizes paper-cycle counts and eligibility using
  exact `Decimal` rates. It cannot produce an order or change allocation.
- The existing `ShadowForwardEvaluator` remains the shadow-backtesting path,
  including Brier scoring, Champion/Challenger comparison, drift detection, and
  the terminal no-order sink.

## Framework additions from the 2026-10-04 archive

The four archived screenshots were reviewed against official repositories and
their patterns are now represented in the catalog. No package, Docker service,
credential store, wallet client, or live connector was installed. The replay
import boundary may accept externally recorded data for research, but imported
data remains non-actionable and cannot create an order intent.

Safe additions are NautilusTrader's deterministic event-clock and
adapter-boundary vocabulary; Hummingbot's separation of order-book tracking,
user streams, and connector lifecycle; Freqtrade's dry-run, look-ahead,
recursive-analysis, and performance-reporting checks; and Kronos's
model/challenger evaluation vocabulary for optional OHLCV research.

## Real-money transition knowledge (future gates only)

This is recorded for future planning, not authorization. Completing paper or
shadow testing does not enable live trading. Any future transition would still
require separately verified account eligibility, an external secret store, a
secure signer boundary, venue order/user-stream contracts, restart-safe
reconciliation, deterministic risk limits and circuit breakers, staged shadow
evidence with realistic costs, and a separate explicit operator authorization.
Until then, `LIVE_TRADING_ENABLED=false` remains authoritative and every
real-order path must fail closed. No private key, wallet credential, exchange
secret, or activation token belongs in project memory or repository files.
