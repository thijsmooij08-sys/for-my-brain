from dataclasses import dataclass
from decimal import Decimal

from polytrader.opportunities.engine import Opportunity
from polytrader.risk.manager import RiskDecision


@dataclass(frozen=True, slots=True)
class OrderIntent:
    action_id: str
    market_id: str
    token_id: str
    side: str
    quantity: Decimal
    limit_price: Decimal

    @classmethod
    def from_approved(cls, opportunity: Opportunity, quantity: Decimal, decision: RiskDecision) -> "OrderIntent":
        if not decision.approved:
            raise PermissionError("RiskManager approval is required to create an OrderIntent")
        if quantity <= 0:
            raise ValueError("order intent quantity must be positive")
        return cls(
            opportunity.action_id, opportunity.market_id, opportunity.token_id, opportunity.side,
            quantity, opportunity.executable_price,
        )
