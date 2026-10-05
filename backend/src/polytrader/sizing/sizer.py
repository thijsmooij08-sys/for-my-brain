from dataclasses import dataclass
from decimal import Decimal

from polytrader.opportunities.engine import Opportunity


@dataclass(frozen=True, slots=True)
class PositionSizeDecision:
    quantity: Decimal
    notional: Decimal


class PositionSizer:
    def __init__(self, max_order_notional: Decimal) -> None:
        self.max_order_notional = max_order_notional

    def size(self, opportunity: Opportunity) -> PositionSizeDecision:
        if opportunity.net_edge <= 0:
            return PositionSizeDecision(Decimal("0"), Decimal("0"))
        quantity = self.max_order_notional / opportunity.executable_price
        return PositionSizeDecision(quantity, quantity * opportunity.executable_price)
