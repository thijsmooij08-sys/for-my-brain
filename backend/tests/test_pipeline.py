from datetime import UTC, datetime
from decimal import Decimal

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.opportunities.engine import OpportunityEngine
from polytrader.orders.intent import OrderIntent
from polytrader.risk.manager import RiskDecision
from polytrader.sizing.sizer import PositionSizer
from polytrader.strategies.development import DevelopmentStrategy
from polytrader.strategies.scanner import scan_public_markets


class FakePublicSource:
    async def list_markets(self, limit: int = 20):
        from polytrader.integrations.polymarket.adapter import MarketSummary
        return [MarketSummary("m", "c", "Question", "OPEN", "yes", "no")]

    async def order_book(self, token_id: str):
        return OrderBook(token_id, (), (BookLevel(Decimal("0.50"), Decimal("10")),))


def test_development_signal_becomes_sized_opportunity() -> None:
    book = OrderBook(
        "yes",
        (BookLevel(Decimal("0.48"), Decimal("100")),),
        (BookLevel(Decimal("0.50"), Decimal("100")),),
    )
    signal = DevelopmentStrategy(fair_probability=Decimal("0.60")).analyze(
        market_id="market-1", token_id="yes", book=book, observed_at=datetime.now(UTC)
    )
    opportunity = OpportunityEngine().from_signal(signal, book)
    size = PositionSizer(max_order_notional=Decimal("10")).size(opportunity)

    assert signal.action == "BUY"
    assert opportunity.net_edge == Decimal("0.10")
    assert size.quantity == Decimal("20")
    assert size.notional == Decimal("10.00")


def test_order_intent_requires_an_approved_risk_decision() -> None:
    opportunity = OpportunityEngine().from_signal(
        DevelopmentStrategy(Decimal("0.60")).analyze(
            "market-1", "yes", OrderBook("yes", (), (BookLevel(Decimal("0.50"), Decimal("100")),)), datetime.now(UTC)
        ),
        OrderBook("yes", (), (BookLevel(Decimal("0.50"), Decimal("100")),)),
    )
    intent = OrderIntent.from_approved(opportunity, Decimal("2"), RiskDecision(True, "APPROVED", "test"))
    assert intent.side == "BUY"
    assert intent.quantity == Decimal("2")


def test_public_scanner_stops_at_signals_without_execution() -> None:
    import asyncio
    signals = asyncio.run(scan_public_markets(
        FakePublicSource(), DevelopmentStrategy(Decimal("0.60")), datetime.now(UTC), limit=1,
    ))
    assert len(signals) == 1
    assert signals[0].token_id == "yes"
