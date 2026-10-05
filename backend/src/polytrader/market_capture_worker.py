"""Continuously retain public Polymarket books for future replay research.

This worker is deliberately read-only. It uses only the public adapter and
the evidence repository; it never constructs a secure client or an order
intent. A process restart is safe because evidence writes are idempotent.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass

from polytrader.integrations.polymarket.adapter import PolymarketPublicAdapter
from polytrader.market_data.ingestion import SnapshotIngestionService
from polytrader.market_data.streaming import ReconnectingMarketStream, StreamingIngestionService
from polytrader.persistence.repository import PortfolioRepository

log = logging.getLogger("polytrader.market_capture")


@dataclass(frozen=True, slots=True)
class CaptureConfig:
    enabled: bool = True
    database_url: str = "sqlite:////data/polytrader.db"
    market_limit: int = 20
    retry_seconds: int = 30

    @classmethod
    def from_environment(cls) -> "CaptureConfig":
        return cls(
            enabled=os.getenv("MARKET_CAPTURE_ENABLED", "true").lower() in {"1", "true", "yes"},
            database_url=os.getenv("POLYTRADER_DATABASE_URL", "sqlite:////data/polytrader.db"),
            market_limit=max(1, min(int(os.getenv("MARKET_CAPTURE_MARKET_LIMIT", "20")), 100)),
            retry_seconds=max(5, int(os.getenv("MARKET_CAPTURE_RETRY_SECONDS", "30"))),
        )


async def capture_forever(config: CaptureConfig) -> None:
    if not config.enabled:
        log.info("market capture disabled")
        return
    repository = PortfolioRepository(config.database_url)
    adapter = PolymarketPublicAdapter()
    while True:
        try:
            markets = await adapter.list_markets(config.market_limit)
            snapshots = await SnapshotIngestionService(adapter, repository).ingest(config.market_limit)
            token_ids = [market.yes_token_id for market in markets if market.yes_token_id]
            log.info("captured initial snapshots=%d stream_tokens=%d", len(snapshots), len(token_ids))
            if not token_ids:
                await asyncio.sleep(config.retry_seconds)
                continue
            stream = ReconnectingMarketStream(lambda: adapter.stream_market_events(token_ids))
            service = StreamingIngestionService(stream, repository)
            await service.run()
            log.warning("public stream ended; reconnecting")
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("market capture cycle failed; retrying")
            await asyncio.sleep(config.retry_seconds)


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    asyncio.run(capture_forever(CaptureConfig.from_environment()))


if __name__ == "__main__":
    main()
