from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TradeAttribution:
    """Immutable realized round-trip outcome; never an execution authority."""

    attribution_id: str
    trade_id: str
    strategy_version: str
    market_id: str
    token_id: str
    quantity: Decimal
    entry_notional: Decimal
    exit_notional: Decimal
    entry_fee: Decimal
    exit_fee: Decimal
    realized_pnl: Decimal
    return_fraction: Decimal
    observed_at: datetime
    dataset_version: str
    evidence_ids: tuple[str, ...]
    actionable: bool = False

    @classmethod
    def from_round_trip(
        cls, *, trade_id: str, strategy_version: str, market_id: str, token_id: str,
        quantity: Decimal, entry_notional: Decimal, exit_notional: Decimal,
        entry_fee: Decimal, exit_fee: Decimal, observed_at: datetime,
        dataset_version: str, evidence_ids: tuple[str, ...],
    ) -> TradeAttribution:
        if not trade_id or not strategy_version or not market_id or not token_id:
            raise ValueError("trade and strategy identity fields are required")
        if quantity <= 0 or entry_notional <= 0 or exit_notional < 0 or entry_fee < 0 or exit_fee < 0:
            raise ValueError("round-trip values must be non-negative and quantity/notional positive")
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("observed_at must include a timezone")
        pnl = exit_notional - entry_notional - entry_fee - exit_fee
        return_fraction = pnl / entry_notional
        material = "|".join((
            trade_id, strategy_version, market_id, token_id, str(quantity), str(entry_notional),
            str(exit_notional), str(entry_fee), str(exit_fee), observed_at.isoformat(),
            dataset_version, *evidence_ids,
        ))
        attribution_id = hashlib.sha256(material.encode("utf-8")).hexdigest()
        return cls(
            attribution_id, trade_id, strategy_version, market_id, token_id, quantity,
            entry_notional, exit_notional, entry_fee, exit_fee, pnl, return_fraction,
            observed_at, dataset_version, tuple(evidence_ids), False,
        )


class TradeAttributionLedger:
    """Append-only, idempotent JSONL storage for research attribution."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: TradeAttribution) -> None:
        if any(item.attribution_id == record.attribution_id for item in self.read()):
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "attribution_id": record.attribution_id, "trade_id": record.trade_id,
            "strategy_version": record.strategy_version, "market_id": record.market_id,
            "token_id": record.token_id, "quantity": str(record.quantity),
            "entry_notional": str(record.entry_notional), "exit_notional": str(record.exit_notional),
            "entry_fee": str(record.entry_fee), "exit_fee": str(record.exit_fee),
            "realized_pnl": str(record.realized_pnl), "return_fraction": str(record.return_fraction),
            "observed_at": record.observed_at.isoformat(), "dataset_version": record.dataset_version,
            "evidence_ids": list(record.evidence_ids), "actionable": record.actionable,
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def read(self) -> tuple[TradeAttribution, ...]:
        if not self.path.exists():
            return ()
        records: list[TradeAttribution] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            for field in (
                "quantity", "entry_notional", "exit_notional", "entry_fee", "exit_fee",
                "realized_pnl", "return_fraction",
            ):
                value[field] = Decimal(value[field])
            value["observed_at"] = datetime.fromisoformat(value["observed_at"])
            value["evidence_ids"] = tuple(value["evidence_ids"])
            records.append(TradeAttribution(**value))
        return tuple(records)
