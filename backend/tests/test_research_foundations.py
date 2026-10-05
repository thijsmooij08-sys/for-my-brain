from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polytrader.simulation.features import PointInTimeFeatureStore, TimedFeature
from polytrader.simulation.statistics import benjamini_hochberg


def test_feature_store_does_not_return_future_vintage() -> None:
    store = PointInTimeFeatureStore()
    base = datetime(2026, 1, 1, tzinfo=UTC)
    store.add(TimedFeature("spread", base, Decimal("0.10"), "source-a"))
    store.add(TimedFeature("spread", base + timedelta(minutes=1), Decimal("0.20"), "source-b"))
    assert store.as_of("spread", base + timedelta(seconds=30)).value == Decimal("0.10")
    with pytest.raises(KeyError):
        store.as_of("unknown", base)


def test_benjamini_hochberg_controls_discoveries() -> None:
    result = benjamini_hochberg(
        {"a": Decimal("0.001"), "b": Decimal("0.02"), "c": Decimal("0.8")},
        q=Decimal("0.05"),
    )
    assert result.accepted == ("a", "b")
    assert result.threshold == Decimal("0.02")
