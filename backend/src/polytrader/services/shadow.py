from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Protocol

from polytrader.domain.market import OrderBook
from polytrader.integrations.polymarket.adapter import MarketSummary
from polytrader.learning.champion import (
    CandidateEvaluation,
    ChampionChallengerPolicy,
    PromotionDecision,
)
from polytrader.market_data.health import DataHealthMonitor
from polytrader.orders.intent import OrderIntent


class _PublicMarketSource(Protocol):
    async def list_markets(self, limit: int = 20) -> list[MarketSummary]: ...

    async def order_book(self, token_id: str) -> OrderBook: ...


def _utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")


def _hash(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("artifact_hash must be a 64-character hexadecimal digest")


@dataclass(frozen=True, slots=True)
class ShadowForecast:
    forecast_id: str
    market_id: str
    token_id: str
    strategy_version: str
    probability: Decimal
    outcome: Decimal
    source_timestamp: datetime
    observed_at: datetime
    source: str
    dataset_version: str
    artifact_hash: str
    actionable: bool = False

    def __post_init__(self) -> None:
        if not self.forecast_id or not self.market_id or not self.token_id or not self.strategy_version:
            raise ValueError("shadow forecast identity fields are required")
        if not self.source or not self.dataset_version:
            raise ValueError("shadow forecast provenance is required")
        if not Decimal("0") <= self.probability <= Decimal("1"):
            raise ValueError("probability must be between 0 and 1")
        if self.outcome not in (Decimal("0"), Decimal("1")):
            raise ValueError("outcome must be 0 or 1")
        _utc(self.source_timestamp, "source_timestamp")
        _utc(self.observed_at, "observed_at")
        if self.observed_at < self.source_timestamp:
            raise ValueError("observed_at cannot precede source_timestamp")
        _hash(self.artifact_hash)
        if self.actionable:
            raise ValueError("shadow forecasts must remain non-actionable")


@dataclass(frozen=True, slots=True)
class ShadowForwardReport:
    report_id: str
    strategy_version: str
    dataset_version: str
    sample_count: int
    brier_score: Decimal
    evaluated_at: datetime
    data_health: str
    forecast_ids: tuple[str, ...]
    actionable: bool = False

    def __post_init__(self) -> None:
        if self.sample_count <= 0 or len(self.forecast_ids) != self.sample_count:
            raise ValueError("shadow reports require one id per positive sample")
        if not self.strategy_version or not self.dataset_version:
            raise ValueError("shadow report provenance is required")
        if self.brier_score < 0 or self.brier_score > 1:
            raise ValueError("Brier score must be between 0 and 1")
        _utc(self.evaluated_at, "evaluated_at")
        if self.actionable:
            raise ValueError("shadow reports must remain non-actionable")


@dataclass(frozen=True, slots=True)
class PendingShadowForecast:
    forecast_id: str
    market_id: str
    token_id: str
    strategy_version: str
    probability: Decimal
    source_timestamp: datetime
    observed_at: datetime
    source: str
    dataset_version: str
    artifact_hash: str
    actionable: bool = False

    def __post_init__(self) -> None:
        _utc(self.source_timestamp, "source_timestamp")
        _utc(self.observed_at, "observed_at")
        if self.observed_at < self.source_timestamp:
            raise ValueError("observed_at cannot precede source_timestamp")
        if not Decimal("0") <= self.probability <= Decimal("1"):
            raise ValueError("probability must be between 0 and 1")
        if self.actionable:
            raise ValueError("shadow forecasts must remain non-actionable")
        _hash(self.artifact_hash)

    def settle(self, outcome: Decimal, *, observed_at: datetime) -> ShadowForecast:
        return ShadowForecast(
            forecast_id=self.forecast_id,
            market_id=self.market_id,
            token_id=self.token_id,
            strategy_version=self.strategy_version,
            probability=self.probability,
            outcome=outcome,
            source_timestamp=self.source_timestamp,
            observed_at=observed_at,
            source=self.source,
            dataset_version=self.dataset_version,
            artifact_hash=self.artifact_hash,
        )


class ShadowPublicSession:
    """Collect current public books into pending, no-order shadow forecasts."""

    @staticmethod
    async def collect(
        source: _PublicMarketSource,
        *,
        fair_probability: Decimal,
        observed_at: datetime,
        limit: int = 20,
    ) -> tuple[PendingShadowForecast, ...]:
        _utc(observed_at, "observed_at")
        if not Decimal("0") <= fair_probability <= Decimal("1"):
            raise ValueError("fair_probability must be between 0 and 1")
        pending: list[PendingShadowForecast] = []
        for market in await source.list_markets(limit):
            token_id = getattr(market, "yes_token_id", None)
            if not token_id:
                continue
            book = await source.order_book(token_id)
            source_timestamp = book.source_timestamp or book.received_at or observed_at
            payload = (
                f"{market.market_id}|{token_id}|{fair_probability}|{source_timestamp.isoformat()}|"
                f"{[(str(level.price), str(level.quantity)) for level in book.asks]}"
            )
            artifact_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            forecast_id = hashlib.sha256(
                f"{market.market_id}|{token_id}|{observed_at.isoformat()}".encode("utf-8")
            ).hexdigest()
            pending.append(
                PendingShadowForecast(
                    forecast_id=forecast_id,
                    market_id=str(market.market_id),
                    token_id=str(token_id),
                    strategy_version="shadow-fair-probability-1",
                    probability=fair_probability,
                    source_timestamp=source_timestamp,
                    observed_at=observed_at,
                    source="polymarket-public",
                    dataset_version="polymarket-public-forward",
                    artifact_hash=artifact_hash,
                )
            )
        return tuple(pending)


@dataclass(frozen=True, slots=True)
class ShadowComparisonReport:
    champion_report_id: str
    challenger_report_id: str
    decision: PromotionDecision
    evaluated_at: datetime
    actionable: bool = False

    def __post_init__(self) -> None:
        _utc(self.evaluated_at, "evaluated_at")
        if self.actionable or self.decision.actionable:
            raise ValueError("shadow comparisons must remain non-actionable")


@dataclass(frozen=True, slots=True)
class ShadowDriftReport:
    baseline_report_id: str
    current_report_id: str
    baseline_score: Decimal
    current_score: Decimal
    delta: Decimal
    threshold: Decimal
    drifted: bool
    evaluated_at: datetime
    actionable: bool = False

    def __post_init__(self) -> None:
        _utc(self.evaluated_at, "evaluated_at")
        if self.threshold < 0 or self.baseline_score < 0 or self.current_score < 0:
            raise ValueError("drift scores and threshold cannot be negative")
        if self.actionable:
            raise ValueError("shadow drift reports must remain non-actionable")


class ShadowForwardJournal:
    """Append-only, idempotent journal for shadow evidence."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, report: ShadowForwardReport) -> None:
        if report.report_id in {item.report_id for item in self.read()}:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        value = asdict(report)
        value["brier_score"] = str(report.brier_score)
        value["evaluated_at"] = report.evaluated_at.isoformat()
        value["forecast_ids"] = list(report.forecast_ids)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(value, sort_keys=True) + "\n")

    def read(self) -> tuple[ShadowForwardReport, ...]:
        if not self.path.exists():
            return ()
        reports: list[ShadowForwardReport] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            value["brier_score"] = Decimal(value["brier_score"])
            value["evaluated_at"] = datetime.fromisoformat(value["evaluated_at"])
            value["forecast_ids"] = tuple(value["forecast_ids"])
            reports.append(ShadowForwardReport(**value))
        return tuple(reports)


class ShadowForwardEvaluator:
    def __init__(self, *, health_monitor: DataHealthMonitor, journal: ShadowForwardJournal) -> None:
        self.health_monitor = health_monitor
        self.journal = journal

    def evaluate(self, forecasts: list[ShadowForecast], *, now: datetime) -> ShadowForwardReport:
        if not forecasts:
            raise ValueError("at least one shadow forecast is required")
        _utc(now, "now")
        versions = {item.strategy_version for item in forecasts}
        datasets = {item.dataset_version for item in forecasts}
        if len(versions) != 1 or len(datasets) != 1:
            raise ValueError("a report must contain one strategy and dataset version")
        for item in forecasts:
            status = self.health_monitor.evaluate(item.source_timestamp, now)
            if not status.can_open_exposure:
                raise ValueError(f"shadow data is not fresh: {status.reason}")
        score = sum((item.probability - item.outcome) ** 2 for item in forecasts) / Decimal(len(forecasts))
        report_id = hashlib.sha256(
            "|".join(sorted(item.forecast_id for item in forecasts)).encode("utf-8")
        ).hexdigest()
        return ShadowForwardReport(
            report_id=report_id,
            strategy_version=next(iter(versions)),
            dataset_version=next(iter(datasets)),
            sample_count=len(forecasts),
            brier_score=score,
            evaluated_at=now,
            data_health="FRESH",
            forecast_ids=tuple(item.forecast_id for item in forecasts),
        )

    def persist(self, report: ShadowForwardReport) -> None:
        self.journal.append(report)

    @staticmethod
    def compare(
        champion: ShadowForwardReport,
        challenger: ShadowForwardReport,
        *,
        policy: ChampionChallengerPolicy,
    ) -> ShadowComparisonReport:
        if champion.dataset_version != challenger.dataset_version:
            raise ValueError("Champion/Challenger reports require the same dataset version")
        # The policy maximizes score; forward accuracy is therefore 1 - Brier.
        decision = policy.compare(
            champion=CandidateEvaluation(
                "champion", champion.strategy_version, Decimal("1") - champion.brier_score,
                champion.sample_count, champion.report_id,
            ),
            challenger=CandidateEvaluation(
                "challenger", challenger.strategy_version, Decimal("1") - challenger.brier_score,
                challenger.sample_count, challenger.report_id,
            ),
        )
        return ShadowComparisonReport(
            champion_report_id=champion.report_id,
            challenger_report_id=challenger.report_id,
            decision=decision,
            evaluated_at=max(champion.evaluated_at, challenger.evaluated_at),
        )

    @staticmethod
    def drift(
        baseline: ShadowForwardReport,
        current: ShadowForwardReport,
        *,
        threshold: Decimal,
    ) -> ShadowDriftReport:
        if threshold < 0:
            raise ValueError("drift threshold cannot be negative")
        delta = abs(current.brier_score - baseline.brier_score)
        return ShadowDriftReport(
            baseline_report_id=baseline.report_id,
            current_report_id=current.report_id,
            baseline_score=baseline.brier_score,
            current_score=current.brier_score,
            delta=delta,
            threshold=threshold,
            drifted=delta > threshold,
            evaluated_at=max(baseline.evaluated_at, current.evaluated_at),
        )


@dataclass(frozen=True, slots=True)
class ShadowOrderResult:
    action_id: str
    accepted: bool
    reason: str


class ShadowOrderSink:
    """Terminal sink for shadow mode; it records rejection but never submits."""

    def __init__(self) -> None:
        self.submitted: tuple[OrderIntent, ...] = ()

    def submit(self, intent: OrderIntent) -> ShadowOrderResult:
        return ShadowOrderResult(intent.action_id, False, "SHADOW_NO_ORDER")
