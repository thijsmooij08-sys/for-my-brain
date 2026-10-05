from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polytrader.intelligence.models import EvidenceRef


@dataclass(frozen=True, slots=True)
class EventObservation:
    event_id: str
    timestamp: datetime
    evidence: EvidenceRef


@dataclass(frozen=True, slots=True)
class EventStudyResult:
    event_id: str
    sample_size: int
    average_forward_return: Decimal
    evidence_ids: tuple[str, ...]
    model_version: str = "event-study.v1"


class EventStudyEngine:
    def run(self, events: tuple[EventObservation, ...], prices: tuple[tuple[datetime, Decimal], ...]) -> EventStudyResult:
        if not events or not prices:
            raise ValueError("events and prices are required")
        ordered = tuple(sorted(prices, key=lambda item: item[0]))
        returns: list[Decimal] = []
        for event in events:
            before = [price for timestamp, price in ordered if timestamp <= event.timestamp]
            after = [price for timestamp, price in ordered if timestamp > event.timestamp]
            if not before or not after:
                raise ValueError("event requires both pre-event and post-event prices")
            if before[-1] <= 0:
                raise ValueError("prices must be positive")
            returns.append((after[0] - before[-1]) / before[-1])
        average = sum(returns, Decimal("0")) / Decimal(len(returns))
        return EventStudyResult(events[0].event_id, len(returns), average, tuple(e.evidence.evidence_id for e in events))
