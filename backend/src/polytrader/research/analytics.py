"""Optional analytics adapters with an explicit Decimal boundary.

Third-party research libraries operate on pandas/numpy floats. They are kept
behind this module and their output is advisory only; execution and accounting
remain native PolyTrader code using Decimal.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any


def _float_series(values: Iterable[Decimal]) -> Any:
    import pandas as pd

    values = list(values)
    return pd.Series(
        [float(value) for value in values],
        index=pd.date_range("2000-01-01", periods=len(values), freq="D"),
        dtype="float64",
    )


def performance_summary(returns: Iterable[Decimal]) -> dict[str, Decimal]:
    """Return a small, deterministic summary for a Decimal return series.

    QuantStats is used when available for annualized metrics, while the
    canonical values are converted back to Decimal immediately. Empty input is
    rejected so a report cannot look valid without observations.
    """

    values = list(returns)
    if not values:
        raise ValueError("at least one return is required")
    series = _float_series(values)
    try:
        import quantstats as qs

        sharpe = float(qs.stats.sharpe(series, periods=1, annualize=False) or 0.0)
        prices = (series + 1).cumprod()
        max_drawdown = float(qs.stats.max_drawdown(prices) or 0.0)
    except ImportError:
        sharpe = 0.0
        max_drawdown = 0.0
    total_return = Decimal(1)
    for value in values:
        total_return *= Decimal(1) + value
    total_return -= Decimal(1)
    return {
        "total_return": total_return,
        "sharpe": Decimal(str(sharpe)),
        "max_drawdown": Decimal(str(max_drawdown)),
    }


def portfolio_weights(expected_returns: Mapping[str, Decimal]) -> dict[str, Decimal]:
    """Produce long-only research weights, never an executable order.

    PyPortfolioOpt is intentionally used only as a suggestion generator. The
    result is normalized and converted to Decimal before crossing the boundary.
    """

    if not expected_returns:
        return {}
    try:
        from pypfopt import EfficientFrontier
    except ImportError:
        equal = Decimal(1) / Decimal(len(expected_returns))
        return {key: equal for key in expected_returns}
    import numpy as np

    tickers = list(expected_returns)
    mu = np.array([float(expected_returns[key]) for key in tickers], dtype=float)
    cov = np.eye(len(tickers), dtype=float)
    optimizer = EfficientFrontier(mu, cov)
    optimizer.max_sharpe()
    cleaned = optimizer.clean_weights()
    raw = {key: Decimal(str(cleaned.get(key, 0.0))) for key in tickers}  # type: ignore[reportUnknownMemberType]
    total = sum(raw.values(), Decimal(0))
    if not total:
        equal = Decimal(1) / Decimal(len(tickers))
        return {key: equal for key in tickers}
    return {key: (value / total if total else Decimal(0)) for key, value in raw.items()}
