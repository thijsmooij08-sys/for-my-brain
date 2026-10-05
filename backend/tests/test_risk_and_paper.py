from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.execution.paper import LiveTradingDisabledError, PaperExecutionEngine
from polytrader.risk.manager import RiskConfig, RiskManager


def test_risk_approves_then_rejects_duplicate_and_wide_spread() -> None:
    risk = RiskManager(RiskConfig(max_order_notional=Decimal("10"), max_spread=Decimal("0.05")))
    now = datetime.now(UTC)
    approved = risk.evaluate("action-1", Decimal("5"), Decimal("0.02"), now)
    duplicate = risk.evaluate("action-1", Decimal("5"), Decimal("0.02"), now)
    wide = risk.evaluate("action-2", Decimal("5"), Decimal("0.06"), now)
    assert approved.approved is True
    assert duplicate.reason_code == "DUPLICATE_ACTION"
    assert wide.reason_code == "SPREAD_TOO_WIDE"


def test_risk_rejects_stale_data_and_kill_switch() -> None:
    now = datetime.now(UTC)
    stale = RiskManager(RiskConfig(max_data_age_seconds=30)).evaluate(
        "a", Decimal("1"), Decimal("0.01"), now - timedelta(seconds=31)
    )
    killed = RiskManager(RiskConfig(kill_switch=True)).evaluate("b", Decimal("1"), Decimal("0.01"), now)
    assert stale.reason_code == "DATA_STALE"
    assert killed.reason_code == "KILL_SWITCH"


def test_risk_rejects_exposure_liquidity_and_daily_loss_limits() -> None:
    now = datetime.now(UTC)
    config = RiskConfig(
        max_total_exposure=Decimal("100"), max_market_exposure=Decimal("50"),
        minimum_liquidity=Decimal("20"), daily_loss_limit=Decimal("10"),
    )
    risk = RiskManager(config)
    total = risk.evaluate("total", Decimal("2"), Decimal("0.01"), now, current_total_exposure=Decimal("99"))
    market = risk.evaluate("market", Decimal("2"), Decimal("0.01"), now, current_market_exposure=Decimal("49"))
    liquid = risk.evaluate("liquid", Decimal("2"), Decimal("0.01"), now, liquidity=Decimal("19"))
    loss = risk.evaluate(
        "loss", Decimal("2"), Decimal("0.01"), now,
        liquidity=Decimal("20"), realized_daily_loss=Decimal("10"),
    )
    assert total.reason_code == "MAX_TOTAL_EXPOSURE"
    assert market.reason_code == "MAX_MARKET_EXPOSURE"
    assert liquid.reason_code == "INSUFFICIENT_LIQUIDITY"
    assert loss.reason_code == "DAILY_LOSS_LIMIT"


def test_paper_execution_consumes_book_and_updates_exact_accounting() -> None:
    engine = PaperExecutionEngine(Decimal("10"), fee_rate=Decimal("0.01"))
    book = OrderBook("yes", (BookLevel(Decimal("0.50"), Decimal("10")),), (BookLevel(Decimal("0.60"), Decimal("3")),))
    buy = engine.execute("buy-1", "yes", "BUY", Decimal("4"), book)
    assert buy.filled_quantity == Decimal("3")
    assert buy.fee == Decimal("0.018")
    assert buy.average_price == Decimal("0.60")
    assert engine.cash == Decimal("8.182")
    sell = engine.execute("sell-1", "yes", "SELL", Decimal("2"), book)
    assert sell.realized_pnl == Decimal("-0.222")
    assert engine.position_quantity("yes") == Decimal("1")
    assert engine.market_exposure("yes") == Decimal("0.6060")
    assert engine.total_exposure() == Decimal("0.6060")


def test_paper_execution_rejects_sell_beyond_owned_and_live_is_impossible() -> None:
    engine = PaperExecutionEngine(Decimal("10"))
    book = OrderBook("yes", (BookLevel(Decimal("0.50"), Decimal("10")),), (BookLevel(Decimal("0.60"), Decimal("10")),))
    with pytest.raises(ValueError, match="owned"):
        engine.execute("sell", "yes", "SELL", Decimal("1"), book)
    with pytest.raises(LiveTradingDisabledError):
        engine.submit_live_order()


def test_unrealized_pnl_and_equity_reconcile_to_executable_bid() -> None:
    engine = PaperExecutionEngine(Decimal("10"))
    entry = OrderBook("yes", (), (BookLevel(Decimal("0.50"), Decimal("2")),))
    mark = OrderBook("yes", (BookLevel(Decimal("0.60"), Decimal("2")),), (BookLevel(Decimal("0.62"), Decimal("2")),))
    engine.execute("buy", "yes", "BUY", Decimal("2"), entry)
    assert engine.unrealized_pnl("yes", mark) == Decimal("0.20")
    assert engine.equity({"yes": mark}) == Decimal("10.20")


def test_paper_execution_restores_ledger_projection_after_restart() -> None:
    engine = PaperExecutionEngine(Decimal("10"))
    engine.restore(
        cash=Decimal("8.80"),
        positions={"yes": (Decimal("2"), Decimal("1.20"))},
    )
    assert engine.cash == Decimal("8.80")
    assert engine.positions() == {"yes": (Decimal("2"), Decimal("1.20"))}
    with pytest.raises(ValueError, match="negative"):
        engine.restore(cash=Decimal("-1"), positions={})
