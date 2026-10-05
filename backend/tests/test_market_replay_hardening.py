from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from polytrader.simulation.microstructure import ConservativeQueueModel
from polytrader.simulation.quality import ReplayQualityAnalyzer
from polytrader.simulation.replay import ReplayEvent


def _event(sequence: int, source_seconds: int, collected_seconds: int) -> ReplayEvent:
    source = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=source_seconds)
    collected = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=collected_seconds)
    return ReplayEvent(
        event_id=f"e-{sequence}-{source_seconds}", sequence=sequence,
        source_timestamp=source, collected_at=collected, token_id="t1", kind="book",
        payload={"price": "0.50"}, payload_hash="a" * 64,
    )


def test_conservative_queue_estimate_only_fills_after_queue_ahead() -> None:
    estimate = ConservativeQueueModel.estimate(
        requested_quantity=Decimal("4"), queue_ahead=Decimal("3"), traded_volume=Decimal("5")
    )

    assert estimate.filled_quantity == Decimal("2")
    assert estimate.remaining_quantity == Decimal("2")
    assert estimate.queue_remaining == Decimal("0")


def test_replay_quality_reports_ordering_duplicates_and_collection_lag() -> None:
    report = ReplayQualityAnalyzer.analyze(
        (_event(1, 2, 3), _event(1, 1, 4), _event(2, 3, 5))
    )

    assert report.event_count == 3
    assert report.duplicate_sequence_count == 1
    assert report.out_of_order_count == 1
    assert report.max_collection_lag == timedelta(seconds=3)
    assert report.actionable is False
