from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polytrader.intelligence.models import EvidenceRef, IntelligenceOutput


@dataclass(frozen=True, slots=True)
class ValuationScenario:
    name: str
    value: Decimal
    evidence: EvidenceRef

    def __post_init__(self) -> None:
        if not self.name or self.value < 0:
            raise ValueError("valuation scenario is invalid")


class ValuationEngine:
    def evaluate(self, subject_id: str, *, scenarios: tuple[ValuationScenario, ...],
                 as_of: datetime) -> IntelligenceOutput:
        if not scenarios:
            raise ValueError("at least one valuation scenario is required")
        values = {scenario.name: scenario.value for scenario in scenarios}
        evidence = tuple(dict.fromkeys(scenario.evidence for scenario in scenarios))
        low, high = min(values.values()), max(values.values())
        disagreement = high - low
        score = sum(values.values(), Decimal("0")) / Decimal(len(values))
        return IntelligenceOutput(
            engine="valuation", subject_id=subject_id, as_of=as_of, score=score,
            confidence=Decimal("0.25"), components=values, disagreement=disagreement,
            evidence=evidence, model_version="valuation.v1", limitations=("assumptions-required",),
        )
