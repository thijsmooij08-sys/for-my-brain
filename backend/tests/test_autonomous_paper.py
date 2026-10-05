import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.execution.paper import PaperExecutionEngine
from polytrader.integrations.polymarket.adapter import MarketSummary
from polytrader.persistence.repository import PortfolioRepository
from polytrader.risk.manager import RiskConfig, RiskManager
from polytrader.services.paper_loop import AutonomousPaperTrader
from polytrader.services.review import PaperReviewJournal
from polytrader.services.trading import PaperTradingService
from polytrader.sizing.sizer import PositionSizer
from polytrader.strategies.development import DevelopmentStrategy


class Source:
    async def list_markets(self, limit: int = 20) -> list[MarketSummary]:
        return [MarketSummary("m1", "c1", "Test", "active", "yes", "no")]

    async def order_book(self, token_id: str) -> OrderBook:
        return OrderBook("yes", (BookLevel(Decimal("0.45"), Decimal("10")),),
                          (BookLevel(Decimal("0.50"), Decimal("10")),),
                          source_timestamp=datetime.now(UTC) - timedelta(seconds=1),
                          received_at=datetime.now(UTC))


class OfficialStateSource(Source):
    async def list_markets(self, limit: int = 20) -> list[MarketSummary]:
        return [MarketSummary("m1", "c1", "Test", "active=True closed=False accepting_orders=True", "yes", "no")]


def test_autonomous_cycle_runs_scan_analyze_rank_size_risk_and_paper_buy(tmp_path) -> None:
    repo = PortfolioRepository(f"sqlite:///{tmp_path / 'loop.db'}")
    engine = PaperExecutionEngine(Decimal("10"))
    trader = AutonomousPaperTrader(
        source=Source(), strategy=DevelopmentStrategy(Decimal("0.60")),
        sizer=PositionSizer(Decimal("1")), risk=RiskManager(RiskConfig(max_order_notional=Decimal("1"))),
        service=PaperTradingService(engine, repo),
    )
    report = asyncio.run(trader.run_cycle(datetime.now(UTC), limit=10))
    assert report.status == "COMPLETED"
    assert report.buy_count == 1
    assert engine.position_quantity("yes") == Decimal("2")
    assert len(repo.fills()) == 1


def test_autonomous_cycle_accepts_official_sdk_active_state_string(tmp_path) -> None:
    repo = PortfolioRepository(f"sqlite:///{tmp_path / 'sdk-state.db'}")
    trader = AutonomousPaperTrader(
        source=OfficialStateSource(), strategy=DevelopmentStrategy(Decimal("0.60")),
        sizer=PositionSizer(Decimal("1")), risk=RiskManager(RiskConfig(max_order_notional=Decimal("1"))),
        service=PaperTradingService(PaperExecutionEngine(Decimal("10")), repo),
    )
    report = asyncio.run(trader.run_cycle(datetime.now(UTC)))
    assert report.eligible == 1
    assert report.buy_count == 1


def test_kill_switch_stops_cycle_without_execution(tmp_path) -> None:
    repo = PortfolioRepository(f"sqlite:///{tmp_path / 'kill.db'}")
    trader = AutonomousPaperTrader(
        source=Source(), strategy=DevelopmentStrategy(Decimal("0.60")),
        sizer=PositionSizer(Decimal("1")), risk=RiskManager(RiskConfig(kill_switch=True)),
        service=PaperTradingService(PaperExecutionEngine(Decimal("10")), repo),
    )
    report = asyncio.run(trader.run_cycle(datetime.now(UTC)))
    assert report.status == "KILLED"
    assert report.buy_count == 0
    assert repo.fills() == []


def test_cycle_rejects_missing_source_timestamp(tmp_path) -> None:
    class MissingTimestampSource(Source):
        async def order_book(self, token_id: str) -> OrderBook:
            return OrderBook("yes", (BookLevel(Decimal("0.45"), Decimal("10")),),
                              (BookLevel(Decimal("0.50"), Decimal("10")),))

    repo = PortfolioRepository(f"sqlite:///{tmp_path / 'missing.db'}")
    engine = PaperExecutionEngine(Decimal("10"))
    trader = AutonomousPaperTrader(
        source=MissingTimestampSource(), strategy=DevelopmentStrategy(Decimal("0.60")),
        sizer=PositionSizer(Decimal("1")), risk=RiskManager(RiskConfig(max_order_notional=Decimal("1"))),
        service=PaperTradingService(engine, repo),
    )
    report = asyncio.run(trader.run_cycle(datetime.now(UTC)))
    assert report.eligible == 0
    assert report.buy_count == 0
    assert "m1:missing-source-timestamp" in report.reasons
    assert repo.fills() == []


def test_journal_makes_cycle_idempotent_across_instances(tmp_path) -> None:
    # Give the source-double a small clock-skew allowance while preserving the
    # monitor's strict future-timestamp rejection.
    observed_at = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=1)
    journal = PaperReviewJournal(tmp_path / "reviews.jsonl")
    first_repo = PortfolioRepository(f"sqlite:///{tmp_path / 'first.db'}")
    first = AutonomousPaperTrader(
        source=Source(), strategy=DevelopmentStrategy(Decimal("0.60")),
        sizer=PositionSizer(Decimal("1")), risk=RiskManager(RiskConfig(max_order_notional=Decimal("1"))),
        service=PaperTradingService(PaperExecutionEngine(Decimal("10")), first_repo), journal=journal,
    )
    assert asyncio.run(first.run_cycle(observed_at)).buy_count == 1
    second_repo = PortfolioRepository(f"sqlite:///{tmp_path / 'second.db'}")
    second = AutonomousPaperTrader(
        source=Source(), strategy=DevelopmentStrategy(Decimal("0.60")),
        sizer=PositionSizer(Decimal("1")), risk=RiskManager(RiskConfig(max_order_notional=Decimal("1"))),
        service=PaperTradingService(PaperExecutionEngine(Decimal("10")), second_repo), journal=journal,
    )
    assert asyncio.run(second.run_cycle(observed_at)).status == "DUPLICATE"
    assert second_repo.fills() == []
