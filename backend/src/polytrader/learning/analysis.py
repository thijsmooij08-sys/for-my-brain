from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class FeatureAblationResult:
    feature: str
    baseline_score: Decimal
    ablated_score: Decimal
    score_delta: Decimal
    dataset_version: str
    strategy_version: str
    actionable: bool = False


@dataclass(frozen=True, slots=True)
class CounterfactualResult:
    baseline_score: Decimal
    counterfactual_score: Decimal
    delta: Decimal
    dataset_version: str
    strategy_version: str
    actionable: bool = False


class FeatureAblationEngine:
    def evaluate(
        self, *, feature: str, baseline_score: Decimal, ablated_score: Decimal,
        dataset_version: str, strategy_version: str,
    ) -> FeatureAblationResult:
        if not feature or not dataset_version or not strategy_version:
            raise ValueError("feature and provenance fields are required")
        return FeatureAblationResult(
            feature, baseline_score, ablated_score, ablated_score - baseline_score,
            dataset_version, strategy_version, False,
        )


class CounterfactualEngine:
    def compare(
        self, *, baseline_score: Decimal, counterfactual_score: Decimal,
        dataset_version: str, strategy_version: str,
    ) -> CounterfactualResult:
        if not dataset_version or not strategy_version:
            raise ValueError("counterfactual provenance fields are required")
        return CounterfactualResult(
            baseline_score, counterfactual_score, counterfactual_score - baseline_score,
            dataset_version, strategy_version, False,
        )
