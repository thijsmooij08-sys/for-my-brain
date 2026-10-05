from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from polytrader.domain.market import BookLevel, OrderBook


@dataclass(frozen=True, slots=True)
class PriceShockScenario:
    name: str
    relative_change: Decimal

    def __post_init__(self) -> None:
        if not self.name or self.relative_change <= Decimal("-1"):
            raise ValueError("scenario name and valid relative change are required")

    def apply(self, book: OrderBook) -> OrderBook:
        factor = Decimal("1") + self.relative_change
        bids = tuple(BookLevel(level.price * factor, level.quantity) for level in book.bids)
        asks = tuple(BookLevel(level.price * factor, level.quantity) for level in book.asks)
        return OrderBook(book.token_id, bids, asks, source_timestamp=book.source_timestamp, received_at=book.received_at)
