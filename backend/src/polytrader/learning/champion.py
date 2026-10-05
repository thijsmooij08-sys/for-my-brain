from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CandidateEvaluation:
    name: str
    version: str
    score: Decimal
    sample_count: int
    artifact_hash: str


@dataclass(frozen=True, slots=True)
class PromotionDecision:
    promote: bool
    selected_version: str
    reason: str
    actionable: bool = False


class ChampionChallengerPolicy:
    """Compare research artifacts without granting execution authority."""

    def __init__(self, *, min_samples: int, min_improvement: Decimal) -> None:
        if min_samples <= 0 or min_improvement < 0:
            raise ValueError("promotion thresholds must be non-negative and samples positive")
        self.min_samples, self.min_improvement = min_samples, min_improvement

    def compare(self, champion: CandidateEvaluation, challenger: CandidateEvaluation) -> PromotionDecision:
        if challenger.sample_count < self.min_samples:
            return PromotionDecision(False, champion.version, "INSUFFICIENT_EVIDENCE")
        if challenger.score < champion.score + self.min_improvement:
            return PromotionDecision(False, champion.version, "INSUFFICIENT_IMPROVEMENT")
        return PromotionDecision(True, challenger.version, "PROMOTION_CANDIDATE")
