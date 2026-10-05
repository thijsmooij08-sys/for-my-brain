import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.integrations.polymarket.adapter import MarketSummary
from polytrader.market_data.ingestion import SnapshotIngestionService
from polytrader.persistence.repository import PortfolioRepository


class FakeProvider:
    async def list_markets(self, limit: int = 20) -> list[MarketSummary]:
        return [MarketSummary("m1", "c1", "Question", "OPEN", "yes", "no")]

    async def order_book(self, token_id: str) -> OrderBook:
        return OrderBook(
            token_id, (BookLevel(Decimal("0.49"), Decimal("3")),),
            (BookLevel(Decimal("0.51"), Decimal("2")),),
        )


def test_snapshot_ingestion_persists_point_in_time_evidence(tmp_path) -> None:
    collected = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    repository = PortfolioRepository(f"sqlite:///{tmp_path / 'ingestion.db'}")
    service = SnapshotIngestionService(FakeProvider(), repository, clock=lambda: collected)
    snapshots = asyncio.run(service.ingest(limit=1))
    assert len(snapshots) == 1
    assert snapshots[0].market_id == "m1"
    assert snapshots[0].source_timestamp == collected
    assert len(repository.evidence()) == 1
    assert repository.evidence()[0].market_id == "m1"


def test_snapshot_ingestion_is_idempotent_for_same_book(tmp_path) -> None:
    collected = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
    repository = PortfolioRepository(f"sqlite:///{tmp_path / 'repeat.db'}")
    service = SnapshotIngestionService(FakeProvider(), repository, clock=lambda: collected)
    asyncio.run(service.ingest(limit=1))
    asyncio.run(service.ingest(limit=1))
    assert len(repository.evidence()) == 1
