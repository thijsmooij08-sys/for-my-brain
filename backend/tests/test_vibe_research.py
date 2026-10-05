from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polytrader.research.debate import DebatePosition, ResearchDebate
from polytrader.services.review import PaperReviewJournal, ReviewRecord, TradeJournalAnalyzer

NOW = datetime(2026, 10, 4, 23, 0, tzinfo=UTC)


def test_research_debate_is_deterministic_and_non_actionable() -> None:
    artifact = ResearchDebate.evaluate(
        topic="market-momentum",
        positions=(
            DebatePosition("agent-a", "hold", Decimal("0.70"), ("e1",)),
            DebatePosition("agent-b", "buy", Decimal("0.90"), ("e2",)),
            DebatePosition("agent-c", "buy", Decimal("0.60"), ("e3",)),
        ),
        dataset_version="dataset-1",
        evaluated_at=NOW,
    )

    assert artifact.consensus == "buy"
    assert artifact.disagreement == Decimal("0.3333333333333333333333333333")
    assert artifact.actionable is False
    assert len(artifact.artifact_hash) == 64


def test_research_debate_rejects_missing_evidence() -> None:
    with pytest.raises(ValueError, match="evidence"):
        ResearchDebate.evaluate(
            topic="market-momentum",
            positions=(DebatePosition("agent-a", "buy", Decimal("0.7"), ()),),
            dataset_version="dataset-1",
            evaluated_at=NOW,
        )


def test_trade_journal_analyzer_returns_decimal_rates(tmp_path) -> None:
    journal = PaperReviewJournal(tmp_path / "reviews.jsonl")
    journal.append(ReviewRecord("c1", "COMPLETED", 4, 2, 1, 1, ("ok",)))
    journal.append(ReviewRecord("c2", "REJECTED", 4, 0, 0, 0, ("stale",)))

    summary = TradeJournalAnalyzer().analyze(journal.read())

    assert summary.cycle_count == 2
    assert summary.completed_count == 1
    assert summary.eligibility_rate == Decimal("0.25")
    assert summary.buy_count == 1
    assert summary.sell_count == 1
    assert summary.actionable is False
