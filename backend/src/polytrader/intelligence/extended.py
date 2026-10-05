from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from polytrader.intelligence.models import EvidenceRef, IntelligenceOutput
from polytrader.simulation.statistics import MultipleTestingResult, benjamini_hochberg


@dataclass(frozen=True, slots=True)
class ResearchClaim:
    name: str
    value: Decimal
    evidence: EvidenceRef


class FundamentalIntelligenceEngine:
    def evaluate(self, subject_id: str, claims: tuple[ResearchClaim, ...], *, as_of: datetime) -> IntelligenceOutput:
        if not claims:
            raise ValueError("fundamental evaluation requires claims")
        return IntelligenceOutput(
            engine="fundamentals", subject_id=subject_id, as_of=as_of,
            score=sum((claim.value for claim in claims), Decimal("0")) / Decimal(len(claims)),
            confidence=Decimal("0.20"), components={claim.name: claim.value for claim in claims},
            disagreement=max(claim.value for claim in claims) - min(claim.value for claim in claims),
            evidence=tuple(dict.fromkeys(claim.evidence for claim in claims)),
            model_version="fundamentals.v1", limitations=("provider-input-required",),
        )


class PeerIntelligenceEngine:
    def compare(self, subject_id: str, peer_values: Mapping[str, Decimal], *, as_of: datetime,
                evidence: tuple[EvidenceRef, ...]) -> IntelligenceOutput:
        if not peer_values or not evidence:
            raise ValueError("peer comparison requires values and evidence")
        values = tuple(peer_values.values())
        return IntelligenceOutput(
            engine="peer", subject_id=subject_id, as_of=as_of,
            score=sum(values, Decimal("0")) / Decimal(len(values)), confidence=Decimal("0.20"),
            components=peer_values, disagreement=max(values) - min(values), evidence=evidence,
            model_version="peer.v1", limitations=("peer-selection-risk",),
        )


class EarningsIntelligenceEngine:
    def surprise(self, subject_id: str, *, actual: Decimal, expected: Decimal,
                 as_of: datetime, evidence: tuple[EvidenceRef, ...]) -> IntelligenceOutput:
        if expected == 0 or not evidence:
            raise ValueError("earnings expectation must be non-zero and evidenced")
        surprise = (actual - expected) / abs(expected)
        return IntelligenceOutput(
            engine="earnings", subject_id=subject_id, as_of=as_of, score=surprise,
            confidence=Decimal("0.20"), components={"actual": actual, "expected": expected, "surprise": surprise},
            disagreement=Decimal("0"), evidence=evidence, model_version="earnings.v1",
            limitations=("provider-input-required",),
        )


class MacroRegimeEngine:
    def classify(self, subject_id: str, indicators: Mapping[str, Decimal], *, as_of: datetime,
                 evidence: tuple[EvidenceRef, ...]) -> IntelligenceOutput:
        if not indicators or not evidence:
            raise ValueError("macro regime requires indicators and evidence")
        score = sum(indicators.values(), Decimal("0")) / Decimal(len(indicators))
        regime = "risk_on" if score > 0 else "risk_off" if score < 0 else "neutral"
        return IntelligenceOutput(
            engine="macro-regime", subject_id=subject_id, as_of=as_of, score=score,
            confidence=Decimal("0.20"), components={**indicators, "regime": regime},
            disagreement=max(indicators.values()) - min(indicators.values()), evidence=evidence,
            model_version="macro.v1", limitations=("provider-input-required",),
        )


class IncomeFactorEngine:
    def score(self, subject_id: str, *, dividend_yield: Decimal, payout_stability: Decimal,
              as_of: datetime, evidence: tuple[EvidenceRef, ...]) -> IntelligenceOutput:
        if dividend_yield < 0 or not Decimal("0") <= payout_stability <= Decimal("1") or not evidence:
            raise ValueError("income factor inputs are invalid")
        score = dividend_yield * payout_stability
        return IntelligenceOutput(
            engine="income", subject_id=subject_id, as_of=as_of, score=score,
            confidence=Decimal("0.20"), components={"dividend_yield": dividend_yield, "payout_stability": payout_stability},
            disagreement=Decimal("0"), evidence=evidence, model_version="income.v1",
            limitations=("provider-input-required",),
        )


@dataclass(frozen=True, slots=True)
class PatternReport:
    hypothesis: str
    effect_size: Decimal
    significance: MultipleTestingResult
    sample_size: int
    status: str = "RESEARCH_ONLY"


class PatternDiscoveryEngine:
    def evaluate(self, hypothesis: str, *, effect_size: Decimal, p_values: Mapping[str, Decimal],
                 sample_size: int, q: Decimal = Decimal("0.05")) -> PatternReport:
        if not hypothesis or sample_size < 1:
            raise ValueError("pattern hypothesis and sample size are required")
        return PatternReport(hypothesis, effect_size, benjamini_hochberg(p_values, q=q), sample_size)
