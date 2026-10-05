"""Optional Prometheus instrumentation for paper-only activity."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

try:
    from prometheus_client import Counter

    PAPER_FILLS: Any = Counter("polytrader_paper_fills_total", "Paper fills recorded")
    PAPER_NOTIONAL: Any = Counter("polytrader_paper_notional", "Paper notional filled")
except ImportError:  # pragma: no cover - exercised only without research extras
    PAPER_FILLS: Any = None
    PAPER_NOTIONAL: Any = None


def record_paper_fill(notional: Decimal) -> None:
    """Record metrics without changing execution/accounting state."""

    if PAPER_FILLS is not None:
        PAPER_FILLS.inc()
        PAPER_NOTIONAL.inc(float(notional))
