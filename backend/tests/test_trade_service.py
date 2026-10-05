from datetime import UTC, datetime
from decimal import Decimal

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.execution.paper import PaperExecutionEngine
from polytrader.opportunities.engine import Opportunity
from polytrader.orders.intent import OrderIntent
from polytrader.persistence.repository import PortfolioRepository
from polytrader.risk.manager import RiskConfig, RiskDecision, RiskManager
from polytrader.services.trading import PaperTradingService, PaperTradingWorkflow
from polytrader.sizing.sizer import PositionSizer
from polytrader.strategies.development import DevelopmentStrategy


def test_approved_order_intent_executes_and_persists_fill(tmp_path) -> None:
    opportunity = Opportunity("m", "yes", "BUY", Decimal("0.50"), Decimal("0.10"), datetime.now(UTC), "a")
    intent = OrderIntent.from_approved(opportunity, Decimal("2"), RiskDecision(True, "APPROVED", "test"))
    service = PaperTradingService(PaperExecutionEngine(Decimal("10")), PortfolioRepository(f"sqlite:///{tmp_path / 'a.db'}"))
    result = service.execute(intent, OrderBook("yes", (), (BookLevel(Decimal("0.50"), Decimal("2")),)))
    assert result.filled_quantity == Decimal("2")
    assert len(service.repository.fills()) == 1


def test_workflow_enforces_strategy_to_risk_to_paper_order(tmp_path) -> None:
    repo = PortfolioRepository(f"sqlite:///{tmp_path / 'workflow.db'}")
    service = PaperTradingService(PaperExecutionEngine(Decimal("10")), repo)
    workflow = PaperTradingWorkflow(
        DevelopmentStrategy(Decimal("0.60")), PositionSizer(Decimal("1")),
        RiskManager(RiskConfig(max_order_notional=Decimal("1"))), service,
    )
    result = workflow.run(
        "market-1", OrderBook("yes", (BookLevel(Decimal("0.48"), Decimal("10")),),
                            (BookLevel(Decimal("0.50"), Decimal("10")),)), datetime.now(UTC),
    )
    assert result.signal.action == "BUY"
    assert result.risk is not None and result.risk.approved
    assert result.intent is not None and result.fill is not None
    assert len(repo.fills()) == 1
