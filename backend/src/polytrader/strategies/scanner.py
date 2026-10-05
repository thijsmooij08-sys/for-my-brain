"""Public-data scanner that stops at signals; it cannot execute orders."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from polytrader.domain.market import OrderBook
from polytrader.integrations.polymarket.adapter import MarketSummary
from polytrader.strategies.development import DevelopmentStrategy, Signal


class PublicMarketSource(Protocol):
    async def list_markets(self, limit: int = 20) -> list[MarketSummary]: ...
    async def order_book(self, token_id: str) -> OrderBook: ...


async def scan_public_markets(
    source: PublicMarketSource,
    strategy: DevelopmentStrategy,
    observed_at: datetime,
    limit: int = 20,
) -> list[Signal]:
    """Fetch public markets/books and emit deterministic research signals."""

    signals: list[Signal] = []
    for market in await source.list_markets(limit):
        if not market.yes_token_id:
            continue
        book = await source.order_book(market.yes_token_id)
        signals.append(strategy.analyze(str(market.market_id), market.yes_token_id, book, observed_at))
    return signals
