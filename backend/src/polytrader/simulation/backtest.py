from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polytrader.simulation.replay import DatasetManifest


def _decimal(value: Decimal) -> str:
    return format(value, "f")


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    starting_cash: Decimal
    ending_equity: Decimal
    total_return: Decimal
    max_drawdown: Decimal
    fees: Decimal

    @classmethod
    def from_equity_curve(cls, *, starting_cash: Decimal, equity_curve: tuple[Decimal, ...],
                          fees: Decimal) -> BacktestMetrics:
        if not equity_curve or starting_cash <= 0 or fees < 0:
            raise ValueError("equity curve, starting cash, and fees are invalid")
        peak = equity_curve[0]
        max_drawdown = Decimal("0")
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            drawdown = peak - equity
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        ending = equity_curve[-1]
        return cls(starting_cash, ending, (ending - starting_cash) / starting_cash, max_drawdown, fees)

    def to_dict(self) -> dict[str, str]:
        return {name: _decimal(value) for name, value in {
            "starting_cash": self.starting_cash, "ending_equity": self.ending_equity,
            "total_return": self.total_return, "max_drawdown": self.max_drawdown, "fees": self.fees,
        }.items()}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> BacktestMetrics:
        return cls(**{name: Decimal(str(value[name])) for name in (
            "starting_cash", "ending_equity", "total_return", "max_drawdown", "fees")})


@dataclass(frozen=True, slots=True)
class BacktestArtifact:
    dataset: DatasetManifest
    strategy_version: str
    fill_model: str
    latency_ms: int
    metrics: BacktestMetrics
    created_at: datetime
    software_version: str = "polytrader.phase3.v1"

    def __post_init__(self) -> None:
        if not self.strategy_version or not self.fill_model or self.latency_ms < 0:
            raise ValueError("backtest provenance fields are required")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must include a timezone")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset.to_dict(), "strategy_version": self.strategy_version,
            "fill_model": self.fill_model, "latency_ms": self.latency_ms,
            "metrics": self.metrics.to_dict(), "created_at": self.created_at.astimezone(UTC).isoformat(),
            "software_version": self.software_version,
        }

    def save(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.to_dict(), sort_keys=True, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        return path

    @classmethod
    def load(cls, path: Path) -> BacktestArtifact:
        value = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            dataset=DatasetManifest.from_dict(value["dataset"]), strategy_version=value["strategy_version"],
            fill_model=value["fill_model"], latency_ms=int(value["latency_ms"]),
            metrics=BacktestMetrics.from_dict(value["metrics"]),
            created_at=datetime.fromisoformat(value["created_at"]), software_version=value["software_version"],
        )
