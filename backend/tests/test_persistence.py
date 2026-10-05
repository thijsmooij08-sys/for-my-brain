from decimal import Decimal

from polytrader.persistence.repository import PortfolioRepository


def test_repository_persists_auditable_paper_fill(tmp_path) -> None:
    repo = PortfolioRepository(f"sqlite:///{tmp_path / 'polytrader.db'}")
    repo.record_fill("order-1", "yes", "BUY", Decimal("2"), Decimal("0.50"), Decimal("0.01"))
    fill = repo.fills()[0]
    assert fill.order_id == "order-1"
    assert Decimal(fill.price) == Decimal("0.50")


def test_state_projection_reconciles_cash_positions_and_realized_pnl(tmp_path) -> None:
    repo = PortfolioRepository(f"sqlite:///{tmp_path / 'state.db'}")
    repo.record_fill("buy", "yes", "BUY", Decimal("2"), Decimal("0.50"), Decimal("0.01"))
    repo.record_fill("sell", "yes", "SELL", Decimal("1"), Decimal("0.60"), Decimal("0.01"))
    state = repo.state(Decimal("10"))
    assert state["cash"] == Decimal("9.58")
    assert state["realized_pnl"] == Decimal("0.085")
    assert state["positions"]["yes"]["quantity"] == Decimal("1")


def test_paper_performance_counts_only_closed_winners_and_losers(tmp_path) -> None:
    repo = PortfolioRepository(f"sqlite:///{tmp_path / 'perf.db'}")
    repo.record_fill("b", "token", "BUY", Decimal("2"), Decimal("0.40"), Decimal("0"))
    repo.record_fill("s1", "token", "SELL", Decimal("1"), Decimal("0.50"), Decimal("0"))
    repo.record_fill("s2", "token", "SELL", Decimal("1"), Decimal("0.30"), Decimal("0"))
    performance = repo.paper_performance(Decimal("100"))
    assert performance["exits"] == 2
    assert performance["wins"] == 1
    assert performance["losses"] == 1
    assert performance["win_rate"] == Decimal("50")
    assert performance["closed_trade_sample"] == 2
    assert performance["realized_pnl"] == Decimal("0.00")
    assert performance["total_fees"] == Decimal("0")
