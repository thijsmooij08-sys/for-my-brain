from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from polytrader.providers.protocols import DataHealth


@dataclass(frozen=True, slots=True)
class DataHealthStatus:
    status: DataHealth
    checked_at: datetime
    last_source_timestamp: datetime | None
    reason: str
    can_open_exposure: bool


class DataHealthMonitor:
    def __init__(self, max_age_seconds: int) -> None:
        if max_age_seconds <= 0:
            raise ValueError("max_age_seconds must be positive")
        self.max_age = timedelta(seconds=max_age_seconds)

    def evaluate(self, source_timestamp: datetime, now: datetime) -> DataHealthStatus:
        self._validate_utc(source_timestamp, "source_timestamp")
        self._validate_utc(now, "now")
        if source_timestamp > now:
            return DataHealthStatus(DataHealth.INVALID, now, source_timestamp, "source timestamp is in the future", False)
        stale = now - source_timestamp > self.max_age
        return DataHealthStatus(
            DataHealth.STALE if stale else DataHealth.FRESH, now, source_timestamp,
            "source data exceeded freshness window" if stale else "source data is within freshness window",
            not stale,
        )

    def disconnected(self, reason: str, now: datetime | None = None) -> DataHealthStatus:
        checked = now or datetime.now().astimezone()
        self._validate_utc(checked, "now")
        return DataHealthStatus(DataHealth.DISCONNECTED, checked, None, reason, False)

    def invalid(self, reason: str, now: datetime | None = None) -> DataHealthStatus:
        checked = now or datetime.now().astimezone()
        self._validate_utc(checked, "now")
        return DataHealthStatus(DataHealth.INVALID, checked, None, reason, False)

    @staticmethod
    def _validate_utc(value: datetime, field: str) -> None:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field} must include a timezone")
