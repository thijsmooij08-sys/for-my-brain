from datetime import UTC, datetime
from decimal import Decimal

from polytrader.evidence.models import EvidenceObservation
from polytrader.persistence.repository import PortfolioRepository


def make_observation(revision: str = "r1", payload_hash: str = "a" * 64) -> EvidenceObservation:
    timestamp = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    return EvidenceObservation(
        source="polymarket", source_type="public_clob", source_timestamp=timestamp,
        collected_at=timestamp, value={"best_ask": Decimal("0.51")}, revision=revision,
        payload_hash=payload_hash, market_id="m1", token_id="yes",
    )


def test_evidence_persistence_is_idempotent_for_same_provenance(tmp_path) -> None:
    repository = PortfolioRepository(f"sqlite:///{tmp_path / 'evidence.db'}")
    first = repository.record_evidence(make_observation())
    second = repository.record_evidence(make_observation())
    assert first.id == second.id
    assert len(repository.evidence()) == 1
    assert repository.evidence()[0].value == '{"best_ask": "0.51"}'


def test_evidence_persistence_keeps_distinct_revisions(tmp_path) -> None:
    repository = PortfolioRepository(f"sqlite:///{tmp_path / 'vintages.db'}")
    repository.record_evidence(make_observation())
    repository.record_evidence(make_observation("r2", "b" * 64))
    rows = repository.evidence()
    assert len(rows) == 2
    assert {row.revision for row in rows} == {"r1", "r2"}
