from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polytrader.domain.market import OrderBook
from polytrader.execution.paper import PaperExecutionEngine, PaperFill
from polytrader.opportunities.engine import Opportunity, OpportunityEngine
from polytrader.orders.intent import OrderIntent
from polytrader.persistence.repository import PortfolioRepository
from polytrader.risk.manager import RiskDecision, RiskManager
from polytrader.sizing.sizer import PositionSizeDecision, PositionSizer
from polytrader.strategies.development import DevelopmentStrategy, Signal


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    signal: Signal
    opportunity: Opportunity | None
    sizing: PositionSizeDecision | None
    risk: RiskDecision | None
    intent: OrderIntent | None
    fill: PaperFill | None


class PaperTradingService:
    def __init__(self, engine: PaperExecutionEngine, repository: PortfolioRepository) -> None:
        self.engine = engine
        self.repository = repository

    def execute(self, intent: OrderIntent, book: OrderBook) -> PaperFill:
        fill = self.engine.execute(
            intent.action_id, intent.token_id, intent.side, intent.quantity, book
        )
        if fill.filled_quantity:
            self.repository.record_fill(
                intent.action_id, intent.token_id, intent.side, fill.filled_quantity,
                fill.average_price, fill.fee
            )
        return fill


class PaperTradingWorkflow:
    """The explicit Phase 1 Strategy → Risk → Paper pipeline."""

    def __init__(
        self,
        strategy: DevelopmentStrategy,
        sizer: PositionSizer,
        risk: RiskManager,
        service: PaperTradingService,
    ) -> None:
        self.strategy, self.sizer, self.risk, self.service = strategy, sizer, risk, service

    def run(self, market_id: str, book: OrderBook, observed_at: datetime) -> WorkflowResult:
        signal = self.strategy.analyze(market_id, book.token_id, book, observed_at)
        if signal.action != "BUY":
            return WorkflowResult(signal, None, None, None, None, None)
        opportunity = OpportunityEngine().from_signal(signal, book)
        sizing = self.sizer.size(opportunity)
        if sizing.quantity <= 0:
            return WorkflowResult(signal, opportunity, sizing, None, None, None)
        spread = book.spread()
        liquidity = sum((level.quantity for level in book.asks), Decimal("0"))
        risk = self.risk.evaluate(
            opportunity.action_id, sizing.notional,
            spread if spread is not None else Decimal("1"), observed_at,
            current_total_exposure=self.service.engine.total_exposure(),
            current_market_exposure=self.service.engine.market_exposure(book.token_id),
            liquidity=liquidity,
        )
        if not risk.approved:
            return WorkflowResult(signal, opportunity, sizing, risk, None, None)
        intent = OrderIntent.from_approved(opportunity, sizing.quantity, risk)
        fill = self.service.execute(intent, book)
        return WorkflowResult(signal, opportunity, sizing, risk, intent, fill)
