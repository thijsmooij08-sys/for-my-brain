from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class BookLevel:
    price: Decimal
    quantity: Decimal

    def __post_init__(self) -> None:
        if not Decimal("0") < self.price <= Decimal("1") or self.quantity <= 0:
            raise ValueError("book levels require probability price (0, 1] and positive quantity")


@dataclass(frozen=True, slots=True)
class FillEstimate:
    filled_quantity: Decimal
    remaining_quantity: Decimal
    notional: Decimal

    @property
    def vwap(self) -> Decimal | None:
        return self.notional / self.filled_quantity if self.filled_quantity else None


@dataclass(frozen=True, slots=True)
class OrderBook:
    token_id: str
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    source_timestamp: datetime | None = None
    received_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.token_id:
            raise ValueError("token_id is required")
        if tuple(sorted(self.bids, key=lambda level: level.price, reverse=True)) != self.bids:
            raise ValueError("bids must be descending")
        if tuple(sorted(self.asks, key=lambda level: level.price)) != self.asks:
            raise ValueError("asks must be ascending")
        if self.bids and self.asks and self.bids[0].price >= self.asks[0].price:
            raise ValueError("crossed order book")
        for timestamp, field in ((self.source_timestamp, "source_timestamp"), (self.received_at, "received_at")):
            if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
                raise ValueError(f"{field} must include a timezone")

    def best_bid(self) -> Decimal | None:
        return self.bids[0].price if self.bids else None

    def best_ask(self) -> Decimal | None:
        return self.asks[0].price if self.asks else None

    def spread(self) -> Decimal | None:
        if not self.bids or not self.asks:
            return None
        return self.asks[0].price - self.bids[0].price

    def estimate_buy(self, quantity: Decimal) -> FillEstimate:
        return self._walk(self.asks, quantity)

    def estimate_sell(self, quantity: Decimal) -> FillEstimate:
        return self._walk(self.bids, quantity)

    @staticmethod
    def _walk(levels: tuple[BookLevel, ...], quantity: Decimal) -> FillEstimate:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        remaining, notional = quantity, Decimal("0")
        for level in levels:
            consumed = min(remaining, level.quantity)
            notional += consumed * level.price
            remaining -= consumed
            if remaining == 0:
                break
        return FillEstimate(quantity - remaining, remaining, notional)
