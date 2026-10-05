# Polymarket integration

Last verified: 2026-10-03 UTC. The official [Polymarket Python SDK](https://github.com/Polymarket/py-sdk) is `polymarket-client` **0.12.0**, MIT-licensed, requiring Python >=3.11. Public use will use `AsyncPublicClient`; authenticated `AsyncSecureClient` is out of scope and must not be initialized in Phase 1.

The SDK supplies typed `Market` and `OrderBook` models and public market/order-book calls. Live verification found outcome identity at `market.outcomes.yes/no.token_id` (not an assumed `clob_token_ids` field); the adapter preserves these IDs exactly, normalizes external levels into ascending asks/descending bids, and rejects invalid/stale books. Streaming, rate-limit recovery, secure clients, eligibility, fees, and matching-engine details are documented for later assessment; Phase 1 uses only public request/response data.
