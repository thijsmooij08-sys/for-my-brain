from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from polytrader.domain.market import OrderBook
from polytrader.market_data.streaming import (
    MarketEventEvidence,
    OrderBookStore,
    ReconnectingMarketStream,
    StreamingIngestionService,
)
from polytrader.persistence.repository import PortfolioRepository


def test_order_book_store_applies_snapshot_and_incremental_change() -> None:
    store = OrderBookStore()
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    snapshot = {
        "type": "book",
        "payload": {
            "asset_id": "yes",
            "timestamp": timestamp,
            "bids": [{"price": "0.40", "size": "10"}],
            "asks": [{"price": "0.60", "size": "8"}],
        },
    }
    assert isinstance(store.apply(snapshot, received_at=timestamp), OrderBook)
    changed = {
        "type": "price_change",
        "payload": {
            "timestamp": timestamp,
            "price_changes": [{"asset_id": "yes", "side": "BUY", "price": "0.45", "size": "4"}],
        },
    }
    book = store.apply(changed, received_at=timestamp)
    assert isinstance(book, OrderBook)
    assert book.best_bid() == Decimal("0.45")
    assert book.best_ask() == Decimal("0.60")


def test_reconnecting_stream_retries_after_disconnect() -> None:
    attempts = 0

    async def source():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            yield {"type": "book"}
            raise ConnectionError("dropped")
        yield {"type": "book-again"}

    async def run() -> list[dict[str, str]]:
        stream = ReconnectingMarketStream(lambda: source(), max_reconnects=2, sleep=lambda _: asyncio.sleep(0))
        events = []
        async for event in stream.events():
            events.append(event)
        return events

    assert asyncio.run(run()) == [{"type": "book"}, {"type": "book-again"}]


def test_documented_public_events_are_canonicalized_with_decimal_strings() -> None:
    store = OrderBookStore()
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    events = [
        ({"type": "last_trade_price", "payload": {"asset_id": "yes", "price": Decimal("0.42"), "size": Decimal("3"), "side": "BUY"}}, "last_trade_price"),
        ({"type": "tick_size_change", "payload": {"token_id": "yes", "old_tick_size": Decimal("0.01"), "tick_size": Decimal("0.001")}}, "tick_size_change"),
        ({"type": "best_bid_ask", "payload": {"asset_id": "yes", "best_bid": Decimal("0.41"), "best_ask": Decimal("0.43"), "spread": Decimal("0.02")}}, "best_bid_ask"),
    ]
    for event, event_type in events:
        result = store.apply(event, received_at=timestamp)
        assert isinstance(result, MarketEventEvidence)
        assert result.event_type == event_type
        assert result.token_id == "yes"
        assert all(not isinstance(value, float) for value in result.value.values())


def test_streaming_service_persists_documented_public_events(tmp_path) -> None:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    raw_events = [
        {"type": "last_trade_price", "payload": {"asset_id": "yes", "timestamp": timestamp, "price": "0.42", "size": "3", "side": "BUY"}},
        {"type": "tick_size_change", "payload": {"token_id": "yes", "timestamp": timestamp, "old_tick_size": "0.01", "tick_size": "0.001"}},
        {"type": "best_bid_ask", "payload": {"asset_id": "yes", "timestamp": timestamp, "best_bid": "0.41", "best_ask": "0.43", "spread": "0.02"}},
    ]

    async def source():
        for event in raw_events:
            yield event

    repository = PortfolioRepository(f"sqlite:///{tmp_path / 'stream-events.db'}")
    service = StreamingIngestionService(
        ReconnectingMarketStream(lambda: source()), repository, clock=lambda: timestamp
    )
    assert asyncio.run(service.run()) == 3
    records = repository.evidence()
    assert [record.source_type for record in records] == [
        "public_market_last_trade_price", "public_market_tick_size_change", "public_market_best_bid_ask"
    ]
