from dataclasses import dataclass
from decimal import Decimal

from polytrader.domain.market import OrderBook
from polytrader.strategies.development import Signal


@dataclass(frozen=True, slots=True)
class Opportunity:
    market_id: str
    token_id: str
    side: str
    executable_price: Decimal
    net_edge: Decimal
    data_at: object
    action_id: str


class OpportunityEngine:
    def from_signal(self, signal: Signal, book: OrderBook) -> Opportunity:
        if signal.action != "BUY" or book.best_ask() is None:
            raise ValueError("only actionable buy signals can become an opportunity")
        price = book.best_ask()
        assert price is not None
        return Opportunity(
            signal.market_id, signal.token_id, "BUY", price, signal.fair_probability - price,
            signal.observed_at, f"{signal.strategy_id}:{signal.market_id}:{signal.token_id}:{signal.observed_at.isoformat()}",
        )

    def from_exit(self, market_id: str, token_id: str, book: OrderBook, data_at: object) -> Opportunity:
        price = book.best_bid()
        if price is None:
            raise ValueError("cannot create an exit without an executable bid")
        return Opportunity(
            market_id, token_id, "SELL", price, Decimal("0"), data_at,
            f"exit:{market_id}:{token_id}:{data_at}",
        )
