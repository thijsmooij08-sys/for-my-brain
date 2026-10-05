from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class TimedFeature:
    name: str
    effective_at: datetime
    value: Decimal
    evidence_id: str

    def __post_init__(self) -> None:
        if not self.name or not self.evidence_id or self.effective_at.tzinfo is None:
            raise ValueError("feature identity and timezone-aware effective_at are required")


class PointInTimeFeatureStore:
    def __init__(self) -> None:
        self._features: dict[str, list[TimedFeature]] = {}

    def add(self, feature: TimedFeature) -> None:
        values = self._features.setdefault(feature.name, [])
        values.append(feature)
        values.sort(key=lambda item: item.effective_at)

    def as_of(self, name: str, timestamp: datetime) -> TimedFeature:
        if name not in self._features:
            raise KeyError(name)
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        available = [item for item in self._features[name] if item.effective_at <= timestamp]
        if not available:
            raise KeyError(f"no feature vintage available for {name} at {timestamp.isoformat()}")
        return available[-1]
