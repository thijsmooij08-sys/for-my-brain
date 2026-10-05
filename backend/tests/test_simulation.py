from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.simulation.fills import ReplayFillModel
from polytrader.simulation.replay import (
    DatasetManifest,
    ReplayClock,
    ReplayDataset,
    ReplayEvent,
    ReplayRunner,
)


def _event(sequence: int, seconds: int, value: str = "0.50") -> ReplayEvent:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC) + timedelta(seconds=seconds)
    return ReplayEvent(
        event_id=f"evt-{sequence}", sequence=sequence, source_timestamp=timestamp,
        collected_at=timestamp + timedelta(milliseconds=10), token_id="yes",
        kind="book", payload={"price": value}, payload_hash="a" * 64,
    )


def test_replay_dataset_is_deterministic_and_manifest_is_content_addressed() -> None:
    dataset = ReplayDataset.from_events([_event(2, 2), _event(1, 1)])
    assert [event.sequence for event in dataset.events] == [1, 2]
    assert dataset.manifest.dataset_id == dataset.manifest.content_hash[:16]
    assert DatasetManifest.from_dict(dataset.manifest.to_dict()) == dataset.manifest


def test_replay_clock_rejects_time_travel() -> None:
    clock = ReplayClock(datetime(2026, 1, 1, tzinfo=UTC))
    clock.advance_to(datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC))
    with pytest.raises(ValueError):
        clock.advance_to(datetime(2026, 1, 1, tzinfo=UTC))


def test_book_walking_fill_applies_latency_and_fee() -> None:
    model = ReplayFillModel(fee_rate=Decimal("0.01"), latency=timedelta(seconds=2))
    book = OrderBook(
        "yes", (BookLevel(Decimal("0.40"), Decimal("10")),),
        (BookLevel(Decimal("0.60"), Decimal("3")), BookLevel(Decimal("0.62"), Decimal("4"))),
    )
    fill = model.buy("order-1", Decimal("5"), book, datetime(2026, 1, 1, tzinfo=UTC))
    assert fill.filled_quantity == Decimal("5")
    assert fill.notional == Decimal("3.04")
    assert fill.fee == Decimal("0.0304")
    assert fill.available_at == datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC)


def test_replay_runner_delivers_events_in_point_in_time_order() -> None:
    dataset = ReplayDataset.from_events([_event(2, 2), _event(1, 1)])
    received: list[int] = []
    summary = ReplayRunner(dataset).run(lambda event, clock: received.append(event.sequence))
    assert received == [1, 2]
    assert summary.event_count == 2
    assert summary.dataset_id == dataset.manifest.dataset_id
