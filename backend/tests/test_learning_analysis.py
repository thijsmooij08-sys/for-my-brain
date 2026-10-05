from decimal import Decimal

from polytrader.learning.analysis import CounterfactualEngine, FeatureAblationEngine


def test_feature_ablation_records_exact_delta_and_provenance() -> None:
    result = FeatureAblationEngine().evaluate(
        feature="momentum", baseline_score=Decimal("0.60"), ablated_score=Decimal("0.52"),
        dataset_version="ds-1", strategy_version="s-1",
    )
    assert result.score_delta == Decimal("-0.08")
    assert result.actionable is False


def test_counterfactual_requires_same_dataset_and_is_non_actionable() -> None:
    result = CounterfactualEngine().compare(
        baseline_score=Decimal("0.40"), counterfactual_score=Decimal("0.45"),
        dataset_version="ds-1", strategy_version="s-1",
    )
    assert result.delta == Decimal("0.05")
    assert result.actionable is False
