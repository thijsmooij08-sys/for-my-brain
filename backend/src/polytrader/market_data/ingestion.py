from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime

from polytrader.evidence.models import EvidenceObservation, MarketSnapshot
from polytrader.persistence.repository import PortfolioRepository
from polytrader.providers.protocols import MarketDataProvider


class SnapshotIngestionService:
    """Convert provider responses into canonical, provenance-bearing snapshots."""

    def __init__(
        self,
        provider: MarketDataProvider,
        repository: PortfolioRepository,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.clock = clock or (lambda: datetime.now(UTC))

    async def ingest(self, limit: int = 20) -> list[MarketSnapshot]:
        snapshots: list[MarketSnapshot] = []
        for market in await self.provider.list_markets(limit):
            if not market.yes_token_id:
                continue
            collected_at = self.clock()
            if collected_at.tzinfo is None or collected_at.utcoffset() is None:
                raise ValueError("ingestion clock must return a timezone-aware datetime")
            book = await self.provider.order_book(market.yes_token_id)
            source_timestamp = getattr(book, "source_timestamp", None) or collected_at
            payload = {
                "market_id": market.market_id,
                "condition_id": market.condition_id,
                "question": market.question,
                "status": market.status,
                "yes_token_id": market.yes_token_id,
                "no_token_id": market.no_token_id,
                "bids": [[str(level.price), str(level.quantity)] for level in book.bids],
                "asks": [[str(level.price), str(level.quantity)] for level in book.asks],
            }
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            payload_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
            snapshot = MarketSnapshot(
                market_id=market.market_id, condition_id=market.condition_id,
                question=market.question, status=market.status,
                yes_token_id=market.yes_token_id, no_token_id=market.no_token_id,
                source_timestamp=source_timestamp, collected_at=collected_at,
                bids=tuple((level.price, level.quantity) for level in book.bids),
                asks=tuple((level.price, level.quantity) for level in book.asks),
                payload_hash=payload_hash,
            )
            self.repository.record_evidence(EvidenceObservation(
                source="polymarket", source_type="public_market_snapshot",
                source_timestamp=source_timestamp, collected_at=collected_at,
                value=payload, revision="snapshot", payload_hash=payload_hash,
                market_id=market.market_id, token_id=market.yes_token_id,
            ))
            snapshots.append(snapshot)
        return snapshots
