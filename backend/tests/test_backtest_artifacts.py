from datetime import UTC, datetime
from decimal import Decimal

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.simulation.backtest import BacktestArtifact, BacktestMetrics
from polytrader.simulation.replay import ReplayDataset, ReplayEvent
from polytrader.simulation.scenarios import PriceShockScenario


def _event(sequence: int) -> ReplayEvent:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    return ReplayEvent(
        event_id=f"evt-{sequence}", sequence=sequence, source_timestamp=timestamp,
        collected_at=timestamp, token_id="yes", kind="book", payload={"price": "0.50"},
        payload_hash="a" * 64,
    )


def test_backtest_artifact_round_trips_decimal_metrics(tmp_path) -> None:
    dataset = ReplayDataset.from_events([_event(1)])
    metrics = BacktestMetrics.from_equity_curve(
        starting_cash=Decimal("100.00"),
        equity_curve=(Decimal("100.00"), Decimal("101.50"), Decimal("99.50")),
        fees=Decimal("0.05"),
    )
    artifact = BacktestArtifact(
        dataset=dataset.manifest, strategy_version="strategy.v1", fill_model="book_walk",
        latency_ms=250, metrics=metrics, created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    path = artifact.save(tmp_path / "result.json")
    loaded = BacktestArtifact.load(path)
    assert loaded.metrics == metrics
    assert loaded.dataset.dataset_id == dataset.manifest.dataset_id


def test_price_shock_scenario_preserves_book_ordering() -> None:
    book = OrderBook(
        "yes", (BookLevel(Decimal("0.40"), Decimal("10")),),
        (BookLevel(Decimal("0.60"), Decimal("8")),),
    )
    shocked = PriceShockScenario("downside", Decimal("-0.10")).apply(book)
    assert shocked.best_bid() == Decimal("0.36")
    assert shocked.best_ask() == Decimal("0.54")
