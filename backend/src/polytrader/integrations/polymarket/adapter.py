from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from polymarket.clients import AsyncPublicClient
from polymarket.streams import MarketSpec

from polytrader.domain.market import BookLevel, OrderBook


@dataclass(frozen=True, slots=True)
class MarketSummary:
    market_id: str
    condition_id: str | None
    question: str
    status: str
    yes_token_id: str | None = None
    no_token_id: str | None = None


class PolymarketPublicAdapter:
    """Read-only adapter; never constructs a secure client or submits orders."""

    async def list_markets(self, limit: int = 20) -> list[MarketSummary]:
        async with AsyncPublicClient() as client:
            paginator = client.list_markets(page_size=limit)
            raw = (await paginator.first_page()).items
        summaries: list[MarketSummary] = []
        for market in raw:
            outcomes = getattr(market, "outcomes", None)
            yes = getattr(outcomes, "yes", None) if outcomes is not None else None
            no = getattr(outcomes, "no", None) if outcomes is not None else None
            summaries.append(MarketSummary(
                str(market.id), market.condition_id, market.question or "", str(market.state),
                getattr(yes, "token_id", None), getattr(no, "token_id", None),
            ))
        return summaries

    async def order_book(self, token_id: str) -> OrderBook:
        async with AsyncPublicClient() as client:
            raw = await client.get_order_book(token_id=token_id)
        bids = tuple(sorted((BookLevel(Decimal(str(x.price)), Decimal(str(x.size))) for x in raw.bids), key=lambda x: x.price, reverse=True))
        asks = tuple(sorted((BookLevel(Decimal(str(x.price)), Decimal(str(x.size))) for x in raw.asks), key=lambda x: x.price))
        raw_timestamp = getattr(raw, "timestamp", None)
        source_timestamp = None
        if raw_timestamp is not None:
            if isinstance(raw_timestamp, datetime):
                source_timestamp = raw_timestamp if raw_timestamp.tzinfo else raw_timestamp.replace(tzinfo=UTC)
            else:
                seconds = float(raw_timestamp)
                if seconds > 100_000_000_000:
                    seconds /= 1000
                source_timestamp = datetime.fromtimestamp(seconds, tz=UTC)
        return OrderBook(token_id, bids, asks, source_timestamp=source_timestamp, received_at=datetime.now(UTC))

    async def stream_market_events(self, token_ids: list[str]):
        """Yield public market events using the official SDK market stream.

        The client is deliberately public-only; no credentials or secure client
        are involved. The subscription is closed when the consumer stops.
        """
        async with AsyncPublicClient() as client:
            handle = await client.subscribe(
                MarketSpec(token_ids=token_ids, custom_feature_enabled=True)
            )
            try:
                async for event in handle:
                    yield event
            finally:
                await handle.close()
