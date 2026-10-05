from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polytrader.intelligence.models import EvidenceRef, IntelligenceOutput


@dataclass(frozen=True, slots=True)
class TimedPrice:
    timestamp: datetime
    price: Decimal
    evidence: tuple[EvidenceRef, ...]


class TechnicalFeatureEngine:
    def compute(self, subject_id: str, prices: tuple[TimedPrice, ...], *, as_of: datetime) -> IntelligenceOutput:
        available = tuple(point for point in prices if point.timestamp <= as_of)
        if len(available) < 2:
            raise ValueError("at least two point-in-time prices are required")
        ordered = tuple(sorted(available, key=lambda point: point.timestamp))
        start, end = ordered[0].price, ordered[-1].price
        if start <= 0:
            raise ValueError("prices must be positive")
        momentum = (end - start) / start
        evidence = tuple(ref for point in ordered for ref in point.evidence)
        return IntelligenceOutput(
            engine="technical", subject_id=subject_id, as_of=as_of, score=momentum,
            confidence=Decimal("0.50"), components={"momentum": momentum}, disagreement=Decimal("0"),
            evidence=evidence, model_version="technical.v1", limitations=("research-only",),
        )
