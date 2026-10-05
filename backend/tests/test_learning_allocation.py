from datetime import UTC, datetime
from decimal import Decimal

from polytrader.learning.allocation import AllocationLedger, AllocationProposal, ResearchAllocator


def test_research_allocator_caps_approved_weight_without_execution_authority() -> None:
    decision = ResearchAllocator().propose(
        AllocationProposal("champion", Decimal("0.80"), 50, Decimal("12.50"), Decimal("0.02"))
    )
    assert decision.approved is True
    assert decision.approved_weight == Decimal("0.25")
    assert decision.execution_authority is False


def test_research_allocator_rejects_weak_or_risky_candidate() -> None:
    decision = ResearchAllocator().propose(
        AllocationProposal("challenger", Decimal("0.10"), 29, Decimal("-1"), Decimal("0.06"))
    )
    assert decision.approved is False
    assert decision.approved_weight == Decimal("0")
    assert set(decision.reasons) == {"insufficient_samples", "non_positive_net_pnl", "drawdown_limit"}


def test_allocation_ledger_is_append_only_and_hash_chained(tmp_path) -> None:
    allocator = ResearchAllocator()
    decision = allocator.propose(
        AllocationProposal("champion", Decimal("0.10"), 40, Decimal("2"), Decimal("0.01"))
    )
    ledger = AllocationLedger(tmp_path / "allocation.jsonl")
    first = ledger.append(decision, observed_at=datetime(2026, 10, 5, tzinfo=UTC))
    second = ledger.append(decision, observed_at=datetime(2026, 10, 5, 0, 1, tzinfo=UTC))
    records = ledger.read()
    assert first.record_hash != second.record_hash
    assert records[1]["previous_hash"] == first.record_hash
    assert records[0]["execution_authority"] is False
