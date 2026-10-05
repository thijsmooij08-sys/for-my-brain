from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polytrader.domain.market import OrderBook


@dataclass(frozen=True, slots=True)
class Signal:
    market_id: str
    token_id: str
    action: str
    fair_probability: Decimal
    market_probability: Decimal
    strategy_id: str
    strategy_version: str
    observed_at: datetime
    reason: str


class DevelopmentStrategy:
    """NOT A VALIDATED PROFIT STRATEGY; deterministic plumbing only."""

    def __init__(self, fair_probability: Decimal) -> None:
        self.fair_probability = fair_probability

    def analyze(self, market_id: str, token_id: str, book: OrderBook, observed_at: datetime) -> Signal:
        ask = book.best_ask()
        if ask is None:
            raise ValueError("cannot analyze a book without an executable ask")
        return Signal(
            market_id, token_id, "BUY" if self.fair_probability > ask else "NO_ACTION",
            self.fair_probability, ask, "development", "1", observed_at,
            "Development strategy: NOT A VALIDATED PROFIT STRATEGY",
        )
