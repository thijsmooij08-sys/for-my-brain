from __future__ import annotations

from enum import StrEnum
from typing import Protocol

from polytrader.domain.market import OrderBook
from polytrader.integrations.polymarket.adapter import MarketSummary


class DataHealth(StrEnum):
    FRESH = "FRESH"
    STALE = "STALE"
    DISCONNECTED = "DISCONNECTED"
    INVALID = "INVALID"


class MarketDataProvider(Protocol):
    async def list_markets(self, limit: int = 20) -> list[MarketSummary]: ...

    async def order_book(self, token_id: str) -> OrderBook: ...
