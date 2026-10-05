from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.simulation.fills import ReplayFillModel
from polytrader.simulation.market_costs import PolymarketFeeModel, ResolutionSchedule

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def test_v2_fee_is_decimal_price_sensitive_and_maker_exempt() -> None:
    model = PolymarketFeeModel(fee_rate=Decimal("0.02"))

    assert model.fee(Decimal("100"), Decimal("0.50")) == Decimal("0.50")
    assert model.fee(Decimal("100"), Decimal("0.50"), role="MAKER") == Decimal("0")
    assert model.fee(Decimal("100"), Decimal("0")) == Decimal("0")
    assert model.fee(Decimal("100"), Decimal("1")) == Decimal("0")


def test_v2_fee_rejects_invalid_inputs() -> None:
    model = PolymarketFeeModel(fee_rate=Decimal("0.02"))

    with pytest.raises(ValueError):
        model.fee(Decimal("-1"), Decimal("0.5"))
    with pytest.raises(ValueError):
        model.fee(Decimal("1"), Decimal("1.1"))
    with pytest.raises(ValueError):
        model.fee(Decimal("1"), Decimal("0.5"), role="UNKNOWN")


def test_resolution_schedule_tracks_dispute_lockup() -> None:
    schedule = ResolutionSchedule(
        market_id="m1", resolution_at=NOW, settlement_at=NOW + timedelta(days=2), disputed=True
    )

    assert schedule.is_locked(NOW + timedelta(hours=1)) is True
    assert schedule.is_locked(NOW + timedelta(days=2)) is False
    assert schedule.capital_locked_until == NOW + timedelta(days=2)


def test_resolution_schedule_rejects_time_travel_and_naive_dates() -> None:
    with pytest.raises(ValueError):
        ResolutionSchedule("m1", NOW, NOW - timedelta(seconds=1))
    with pytest.raises(ValueError):
        ResolutionSchedule("m1", datetime(2026, 1, 1), NOW)


def test_replay_fill_can_use_price_sensitive_v2_fee_model() -> None:
    fill = ReplayFillModel(fee_model=PolymarketFeeModel(Decimal("0.02"))).buy(
        "o1", Decimal("2"),
        OrderBook("t1", (), (BookLevel(Decimal("0.50"), Decimal("2")),)), NOW,
    )

    assert fill.notional == Decimal("1.00")
    assert fill.fee == Decimal("0.005")
