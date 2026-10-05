"""Read-only replay dataset quality diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from polytrader.simulation.replay import ReplayEvent


@dataclass(frozen=True, slots=True)
class ReplayQualityReport:
    event_count: int
    duplicate_sequence_count: int
    out_of_order_count: int
    max_collection_lag: timedelta
    actionable: bool = False

    @property
    def clean(self) -> bool:
        return self.duplicate_sequence_count == 0 and self.out_of_order_count == 0


class ReplayQualityAnalyzer:
    """Expose data defects instead of silently hiding them during sorting."""

    @staticmethod
    def analyze(events: Iterable[ReplayEvent]) -> ReplayQualityReport:
        values = tuple(events)
        sequences = [event.sequence for event in values]
        out_of_order = 0
        previous = None
        max_lag = timedelta(0)
        for event in values:
            if previous is not None and event.source_timestamp < previous:
                out_of_order += 1
            previous = event.source_timestamp
            max_lag = max(max_lag, event.collected_at - event.source_timestamp)
        return ReplayQualityReport(
            event_count=len(values),
            duplicate_sequence_count=len(sequences) - len(set(sequences)),
            out_of_order_count=out_of_order,
            max_collection_lag=max_lag,
        )
