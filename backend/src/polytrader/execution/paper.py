from dataclasses import dataclass
from decimal import Decimal

from polytrader.domain.market import OrderBook


class LiveTradingDisabledError(RuntimeError):
    """Raised by the deliberately non-functional live-execution boundary."""


@dataclass(frozen=True, slots=True)
class PaperFill:
    order_id: str
    filled_quantity: Decimal
    fee: Decimal
    average_price: Decimal
    realized_pnl: Decimal


class PaperExecutionEngine:
    def __init__(self, starting_cash: Decimal, fee_rate: Decimal = Decimal("0")) -> None:
        self.cash, self.fee_rate = starting_cash, fee_rate
        self._positions: dict[str, tuple[Decimal, Decimal]] = {}

    def restore(self, *, cash: Decimal, positions: dict[str, tuple[Decimal, Decimal]]) -> None:
        """Restore deterministic paper state reconstructed from the fill ledger.

        The ledger remains authoritative; this only hydrates the in-memory
        execution cache after a process restart. Values are copied and checked
        so callers cannot mutate engine state or restore an invalid portfolio.
        """
        if cash < 0:
            raise ValueError("paper cash cannot be negative")
        restored: dict[str, tuple[Decimal, Decimal]] = {}
        for token_id, (quantity, cost_basis) in positions.items():
            if quantity <= 0 or cost_basis < 0:
                raise ValueError("paper positions must have positive quantity and non-negative cost basis")
            restored[token_id] = (Decimal(quantity), Decimal(cost_basis))
        self.cash = Decimal(cash)
        self._positions = restored

    def position_quantity(self, token_id: str) -> Decimal:
        return self._positions.get(token_id, (Decimal("0"), Decimal("0")))[0]

    def market_exposure(self, token_id: str) -> Decimal:
        return self._positions.get(token_id, (Decimal("0"), Decimal("0")))[1]

    def total_exposure(self) -> Decimal:
        return sum((cost for _, cost in self._positions.values()), Decimal("0"))

    def positions(self) -> dict[str, tuple[Decimal, Decimal]]:
        """Return a copy of paper positions for deterministic management/review."""
        return dict(self._positions)

    def execute(self, order_id: str, token_id: str, side: str, quantity: Decimal, book: OrderBook) -> PaperFill:
        if book.token_id != token_id:
            raise ValueError("order book token mismatch")
        if side not in {"BUY", "SELL"}:
            raise ValueError("side must be BUY or SELL")
        owned, cost_basis = self._positions.get(token_id, (Decimal("0"), Decimal("0")))
        if side == "SELL" and quantity > owned:
            raise ValueError("sell quantity exceeds owned shares")
        estimate = book.estimate_buy(quantity) if side == "BUY" else book.estimate_sell(quantity)
        fee = estimate.notional * self.fee_rate
        if side == "BUY":
            total = estimate.notional + fee
            if total > self.cash:
                raise ValueError("insufficient paper cash")
            self.cash -= total
            new_qty = owned + estimate.filled_quantity
            self._positions[token_id] = (new_qty, cost_basis + total)
            average = estimate.notional / estimate.filled_quantity if estimate.filled_quantity else Decimal("0")
            return PaperFill(order_id, estimate.filled_quantity, fee, average, Decimal("0"))
        cost_removed = cost_basis * estimate.filled_quantity / owned if owned else Decimal("0")
        proceeds = estimate.notional - fee
        self.cash += proceeds
        self._positions[token_id] = (owned - estimate.filled_quantity, cost_basis - cost_removed)
        average = estimate.notional / estimate.filled_quantity if estimate.filled_quantity else Decimal("0")
        return PaperFill(order_id, estimate.filled_quantity, fee, average, proceeds - cost_removed)

    def submit_live_order(self, *args: object, **kwargs: object) -> None:
        raise LiveTradingDisabledError("Live Polymarket execution is impossible in Phase 1")

    def unrealized_pnl(self, token_id: str, book: OrderBook) -> Decimal:
        quantity, cost_basis = self._positions.get(token_id, (Decimal("0"), Decimal("0")))
        mark = book.estimate_sell(quantity).notional
        return mark - cost_basis

    def equity(self, books: dict[str, OrderBook]) -> Decimal:
        marked_positions = sum(
            (books[token_id].estimate_sell(quantity).notional for token_id, (quantity, _) in self._positions.items()),
            Decimal("0"),
        )
        return self.cash + marked_positions
