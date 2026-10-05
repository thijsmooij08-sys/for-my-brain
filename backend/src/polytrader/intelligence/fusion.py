from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from polytrader.intelligence.models import EvidenceRef, IntelligenceOutput


class SignalFusionEngine:
    """Research-only average that retains component disagreement."""

    def fuse(self, subject_id: str, as_of: datetime,
             components: tuple[tuple[str, Decimal, tuple[EvidenceRef, ...]], ...]) -> IntelligenceOutput:
        if not components:
            raise ValueError("at least one component is required")
        scores = tuple(score for _, score, _ in components)
        evidence = tuple(dict.fromkeys(ref for _, _, refs in components for ref in refs))
        if not evidence:
            raise ValueError("fused output requires evidence")
        score = sum(scores, Decimal("0")) / Decimal(len(scores))
        disagreement = max(scores) - min(scores)
        return IntelligenceOutput(
            engine="signal-fusion", subject_id=subject_id, as_of=as_of, score=score,
            confidence=Decimal("0.25"), components={name: value for name, value, _ in components},
            disagreement=disagreement, evidence=evidence, model_version="fusion.v1",
            limitations=("research-only", "component weights are equal"),
        )
