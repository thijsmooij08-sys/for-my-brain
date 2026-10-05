from decimal import Decimal

from polytrader.learning.calibration import CalibrationEngine


def test_calibration_report_uses_exact_decimal_metrics() -> None:
    report = CalibrationEngine(bin_count=2).evaluate(
        ((Decimal("0.25"), 0), (Decimal("0.75"), 1)),
        dataset_version="ds-1", model_version="model-1",
    )
    assert report.sample_count == 2
    assert report.brier_score == Decimal("0.0625")
    assert report.expected_calibration_error == Decimal("0.25")
    assert report.actionable is False


def test_calibration_rejects_probability_outside_unit_interval() -> None:
    try:
        CalibrationEngine().evaluate(((Decimal("1.01"), 1),), dataset_version="ds", model_version="m")
    except ValueError as exc:
        assert "probability" in str(exc)
    else:
        raise AssertionError("invalid probability should be rejected")
