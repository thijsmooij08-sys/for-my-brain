from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from polytrader.domain.market import FillEstimate, OrderBook
from polytrader.simulation.market_costs import PolymarketFeeModel


@dataclass(frozen=True, slots=True)
class ReplayFill:
    order_id: str
    side: str
    requested_quantity: Decimal
    filled_quantity: Decimal
    remaining_quantity: Decimal
    notional: Decimal
    fee: Decimal
    average_price: Decimal
    submitted_at: datetime
    available_at: datetime


class ReplayFillModel:
    """Book-walking fills with explicit fee, slippage, and latency assumptions."""

    def __init__(self, *, fee_rate: Decimal = Decimal("0"), slippage_bps: Decimal = Decimal("0"),
                 latency: timedelta = timedelta(0),
                 fee_model: PolymarketFeeModel | None = None) -> None:
        if fee_rate < 0 or slippage_bps < 0 or latency < timedelta(0):
            raise ValueError("fee, slippage, and latency cannot be negative")
        if fee_model is not None and fee_rate != Decimal("0"):
            raise ValueError("fee_rate and fee_model cannot both be configured")
        self.fee_rate = fee_rate
        self.slippage_bps = slippage_bps
        self.latency = latency
        self.fee_model = fee_model

    def buy(self, order_id: str, quantity: Decimal, book: OrderBook, submitted_at: datetime) -> ReplayFill:
        return self._fill(order_id, "BUY", quantity, book.estimate_buy(quantity), submitted_at)

    def sell(self, order_id: str, quantity: Decimal, book: OrderBook, submitted_at: datetime) -> ReplayFill:
        return self._fill(order_id, "SELL", quantity, book.estimate_sell(quantity), submitted_at)

    def _fill(self, order_id: str, side: str, quantity: Decimal, estimate: FillEstimate,
               submitted_at: datetime) -> ReplayFill:
        if quantity <= 0 or submitted_at.tzinfo is None or submitted_at.utcoffset() is None:
            raise ValueError("quantity must be positive and submitted_at timezone-aware")
        impact = Decimal("1") + self.slippage_bps / Decimal("100000")
        notional = estimate.notional * (impact if side == "BUY" else Decimal("2") - impact)
        average = notional / estimate.filled_quantity if estimate.filled_quantity else Decimal("0")
        fee = (
            self.fee_model.fee(notional, average)
            if self.fee_model is not None
            else notional * self.fee_rate
        )
        return ReplayFill(
            order_id, side, quantity, estimate.filled_quantity, estimate.remaining_quantity,
            notional, fee, average, submitted_at, submitted_at + self.latency,
        )
