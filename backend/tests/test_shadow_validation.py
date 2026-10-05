import asyncio
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.integrations.polymarket.adapter import MarketSummary
from polytrader.learning.champion import CandidateEvaluation, ChampionChallengerPolicy
from polytrader.market_data.health import DataHealthMonitor
from polytrader.orders.intent import OrderIntent
from polytrader.services.shadow import (
    ShadowForecast,
    ShadowForwardEvaluator,
    ShadowForwardJournal,
    ShadowOrderSink,
    ShadowPublicSession,
)

NOW = datetime(2026, 10, 4, 23, 0, tzinfo=timezone.utc)


def forecast(version: str, probability: str, outcome: str, *, forecast_id: str) -> ShadowForecast:
    return ShadowForecast(
        forecast_id=forecast_id,
        market_id="m1",
        token_id="t1",
        strategy_version=version,
        probability=Decimal(probability),
        outcome=Decimal(outcome),
        source_timestamp=NOW,
        observed_at=NOW,
        source="polymarket-public",
        dataset_version="dataset-1",
        artifact_hash="a" * 64,
    )


def test_shadow_evaluator_requires_fresh_data_and_is_idempotent(tmp_path) -> None:
    journal = ShadowForwardJournal(tmp_path / "shadow.jsonl")
    evaluator = ShadowForwardEvaluator(
        health_monitor=DataHealthMonitor(max_age_seconds=60), journal=journal
    )
    report = evaluator.evaluate(
        [forecast("champion", "0.8", "1", forecast_id="f1")],
        now=NOW,
    )
    assert report.brier_score == Decimal("0.04")
    assert report.actionable is False
    evaluator.persist(report)
    evaluator.persist(report)
    assert len(journal.read()) == 1

    with pytest.raises(ValueError, match="fresh"):
        evaluator.evaluate(
            [forecast("champion", "0.8", "1", forecast_id="f2")],
            now=datetime(2026, 10, 4, 23, 2, tzinfo=timezone.utc),
        )


def test_shadow_order_sink_rejects_every_intent() -> None:
    intent = OrderIntent(
        action_id="a1",
        market_id="m1",
        token_id="t1",
        side="BUY",
        quantity=Decimal("1"),
        limit_price=Decimal("0.50"),
    )
    sink = ShadowOrderSink()
    result = sink.submit(intent)
    assert result.accepted is False
    assert result.reason == "SHADOW_NO_ORDER"
    assert sink.submitted == ()


def test_shadow_reports_support_champion_challenger_forward_comparison(tmp_path) -> None:
    journal = ShadowForwardJournal(tmp_path / "shadow.jsonl")
    evaluator = ShadowForwardEvaluator(
        health_monitor=DataHealthMonitor(max_age_seconds=60), journal=journal
    )
    champion = evaluator.evaluate(
        [forecast("champion", "0.6", "1", forecast_id="c1")], now=NOW
    )
    challenger = evaluator.evaluate(
        [forecast("challenger", "0.9", "1", forecast_id="x1")], now=NOW
    )
    decision = ChampionChallengerPolicy(
        min_samples=1, min_improvement=Decimal("0.01")
    ).compare(
        CandidateEvaluation("champion", "c", Decimal("1") - champion.brier_score, 1, "c" * 64),
        CandidateEvaluation("challenger", "x", Decimal("1") - challenger.brier_score, 1, "x" * 64),
    )
    assert decision.promote is True
    assert decision.actionable is False


def test_shadow_comparison_and_drift_reports_are_non_actionable(tmp_path) -> None:
    journal = ShadowForwardJournal(tmp_path / "shadow.jsonl")
    evaluator = ShadowForwardEvaluator(
        health_monitor=DataHealthMonitor(max_age_seconds=60), journal=journal
    )
    champion = evaluator.evaluate(
        [forecast("champion", "0.6", "1", forecast_id="c1")], now=NOW
    )
    challenger = evaluator.evaluate(
        [forecast("challenger", "0.9", "1", forecast_id="x1")], now=NOW
    )
    comparison = evaluator.compare(
        champion,
        challenger,
        policy=ChampionChallengerPolicy(min_samples=1, min_improvement=Decimal("0.01")),
    )
    assert comparison.decision.promote is True
    assert comparison.actionable is False
    drift = evaluator.drift(champion, challenger, threshold=Decimal("0.10"))
    assert drift.drifted is True
    assert drift.delta == Decimal("0.15")
    assert drift.actionable is False


def test_public_shadow_session_collects_current_book_without_ordering() -> None:
    class Source:
        async def list_markets(self, limit: int = 20) -> list[MarketSummary]:
            return [MarketSummary("m1", None, "Question", "OPEN", "t1")]

        async def order_book(self, token_id: str) -> OrderBook:
            return OrderBook(
                token_id,
                (BookLevel(Decimal("0.40"), Decimal("10")),),
                (BookLevel(Decimal("0.50"), Decimal("10")),),
                source_timestamp=NOW,
                received_at=NOW,
            )

    pending = asyncio.run(
        ShadowPublicSession.collect(
            Source(), fair_probability=Decimal("0.60"), observed_at=NOW, limit=1
        )
    )
    assert len(pending) == 1
    assert pending[0].probability == Decimal("0.60")
    assert pending[0].actionable is False
    settled = pending[0].settle(Decimal("1"), observed_at=NOW)
    assert settled.outcome == Decimal("1")
