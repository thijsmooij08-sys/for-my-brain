from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    dataset_version: str
    model_version: str
    sample_count: int
    brier_score: Decimal
    expected_calibration_error: Decimal
    actionable: bool = False


class CalibrationEngine:
    """Compute research-only reliability metrics with exact Decimal arithmetic."""

    def __init__(self, bin_count: int = 10) -> None:
        if bin_count <= 0:
            raise ValueError("bin_count must be positive")
        self.bin_count = bin_count

    def evaluate(
        self, observations: tuple[tuple[Decimal, int], ...], *,
        dataset_version: str, model_version: str,
    ) -> CalibrationReport:
        if not observations:
            raise ValueError("at least one observation is required")
        for probability, outcome in observations:
            if probability < 0 or probability > 1:
                raise ValueError("probability must be between 0 and 1")
            if outcome not in (0, 1):
                raise ValueError("outcome must be 0 or 1")
        count = Decimal(len(observations))
        brier = sum(((probability - Decimal(outcome)) ** 2 for probability, outcome in observations), Decimal("0")) / count
        calibration_error = Decimal("0")
        for bucket in range(self.bin_count):
            lower = Decimal(bucket) / Decimal(self.bin_count)
            upper = Decimal(bucket + 1) / Decimal(self.bin_count)
            members = tuple(
                (probability, outcome) for probability, outcome in observations
                if (lower <= probability < upper) or (bucket == self.bin_count - 1 and probability == 1)
            )
            if members:
                mean_probability = sum((item[0] for item in members), Decimal("0")) / Decimal(len(members))
                mean_outcome = sum((Decimal(item[1]) for item in members), Decimal("0")) / Decimal(len(members))
                calibration_error += (Decimal(len(members)) / count) * abs(mean_probability - mean_outcome)
        return CalibrationReport(dataset_version, model_version, len(observations), brier, calibration_error, False)
