from datetime import UTC, datetime, timedelta

from polytrader.market_data.health import DataHealthMonitor
from polytrader.providers.protocols import DataHealth


def test_health_marks_fresh_and_stale_data() -> None:
    now = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    monitor = DataHealthMonitor(max_age_seconds=30)
    assert monitor.evaluate(now - timedelta(seconds=10), now).status == DataHealth.FRESH
    stale = monitor.evaluate(now - timedelta(seconds=31), now)
    assert stale.status == DataHealth.STALE
    assert stale.reason == "source data exceeded freshness window"


def test_health_transitions_to_disconnected_and_invalid() -> None:
    monitor = DataHealthMonitor(max_age_seconds=30)
    assert monitor.disconnected("socket closed").status == DataHealth.DISCONNECTED
    invalid = monitor.invalid("missing token identity")
    assert invalid.status == DataHealth.INVALID
    assert invalid.reason == "missing token identity"
