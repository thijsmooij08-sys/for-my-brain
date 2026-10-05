from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping


@dataclass(frozen=True, slots=True)
class MultipleTestingResult:
    accepted: tuple[str, ...]
    threshold: Decimal
    q: Decimal
    hypothesis_count: int


def benjamini_hochberg(p_values: Mapping[str, Decimal], *, q: Decimal = Decimal("0.05")) -> MultipleTestingResult:
    if not p_values or q <= 0 or q >= 1:
        raise ValueError("p_values must be non-empty and q must be between zero and one")
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    if any(value < 0 or value > 1 for _, value in ordered):
        raise ValueError("p-values must be between zero and one")
    count = len(ordered)
    passing = [index for index, (_, value) in enumerate(ordered, start=1) if value <= q * index / count]
    if not passing:
        return MultipleTestingResult((), Decimal("0"), q, count)
    rank = max(passing)
    threshold = ordered[rank - 1][1]
    accepted = tuple(name for name, value in ordered if value <= threshold)
    return MultipleTestingResult(accepted, threshold, q, count)
