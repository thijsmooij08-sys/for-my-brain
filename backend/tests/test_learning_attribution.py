from datetime import UTC, datetime
from decimal import Decimal

from polytrader.learning.attribution import TradeAttribution, TradeAttributionLedger


def test_trade_attribution_uses_decimal_pnl_and_provenance() -> None:
    record = TradeAttribution.from_round_trip(
        trade_id="t-1", strategy_version="dev-1", market_id="m1", token_id="yes",
        quantity=Decimal("2"), entry_notional=Decimal("1.00"), exit_notional=Decimal("1.40"),
        entry_fee=Decimal("0.01"), exit_fee=Decimal("0.01"),
        observed_at=datetime(2026, 1, 1, tzinfo=UTC), dataset_version="ds-1",
        evidence_ids=("ev-1",),
    )
    assert record.realized_pnl == Decimal("0.38")
    assert record.return_fraction == Decimal("0.38")
    assert record.evidence_ids == ("ev-1",)
    assert record.actionable is False


def test_attribution_ledger_is_append_only_and_idempotent(tmp_path) -> None:
    path = tmp_path / "attribution.jsonl"
    ledger = TradeAttributionLedger(path)
    record = TradeAttribution.from_round_trip(
        trade_id="t-2", strategy_version="dev-1", market_id="m1", token_id="yes",
        quantity=Decimal("1"), entry_notional=Decimal("0.50"), exit_notional=Decimal("0.60"),
        entry_fee=Decimal("0"), exit_fee=Decimal("0"),
        observed_at=datetime(2026, 1, 1, tzinfo=UTC), dataset_version="ds-1", evidence_ids=(),
    )
    ledger.append(record)
    ledger.append(record)
    assert ledger.read() == (record,)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 1
