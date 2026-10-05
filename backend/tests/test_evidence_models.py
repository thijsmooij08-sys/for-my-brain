from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polytrader.evidence.models import EvidenceObservation, MarketSnapshot


def test_evidence_observation_preserves_provenance_and_utc_vintage() -> None:
    observed = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    collected = datetime(2026, 10, 4, 12, 0, 1, tzinfo=UTC)
    evidence = EvidenceObservation(
        source="polymarket", source_type="public_clob", source_url="https://example.test/book",
        source_timestamp=observed, collected_at=collected, value=Decimal("0.51"),
        revision="r1", payload_hash="a" * 64, market_id="m1", token_id="yes",
        confidence=Decimal("1"), model_version=None,
    )
    assert evidence.source_timestamp == observed
    assert evidence.collected_at == collected
    assert evidence.value == Decimal("0.51")
    assert evidence.payload_hash == "a" * 64


def test_evidence_rejects_naive_timestamp_and_invalid_confidence() -> None:
    with pytest.raises(ValueError, match="timezone"):
        EvidenceObservation(
            source="x", source_type="x", source_timestamp=datetime(2026, 1, 1),
            collected_at=datetime(2026, 1, 1, tzinfo=UTC), value="x", revision="r1",
            payload_hash="a" * 64,
        )
    with pytest.raises(ValueError, match="confidence"):
        EvidenceObservation(
            source="x", source_type="x", source_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
            collected_at=datetime(2026, 1, 1, tzinfo=UTC), value="x", revision="r1",
            payload_hash="a" * 64, confidence=Decimal("1.1"),
        )


def test_market_snapshot_keeps_identity_and_order_book_payload() -> None:
    snapshot = MarketSnapshot(
        market_id="m1", condition_id="c1", question="Question", status="OPEN",
        yes_token_id="yes", no_token_id="no", source_timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        collected_at=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC),
        bids=((Decimal("0.49"), Decimal("3")),),
        asks=((Decimal("0.51"), Decimal("2")),), payload_hash="b" * 64,
    )
    assert snapshot.market_id == "m1"
    assert snapshot.bids[0] == (Decimal("0.49"), Decimal("3"))
