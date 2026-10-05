from decimal import Decimal

from polytrader.research.analytics import performance_summary, portfolio_weights


def test_performance_summary_preserves_decimal_boundary() -> None:
    report = performance_summary([Decimal("0.10"), Decimal("-0.05")])
    assert report["total_return"] == Decimal("0.045")
    assert all(isinstance(value, Decimal) for value in report.values())


def test_portfolio_weights_are_normalized_decimal_suggestions() -> None:
    weights = portfolio_weights({"yes": Decimal("0.1"), "no": Decimal("0.2")})
    assert set(weights) == {"yes", "no"}
    assert sum(weights.values(), Decimal(0)) == Decimal("1")
