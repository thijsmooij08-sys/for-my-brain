from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")


def _require_hash(value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value.lower()):
        raise ValueError("payload_hash must be a 64-character hexadecimal digest")


@dataclass(frozen=True, slots=True)
class EvidenceObservation:
    source: str
    source_type: str
    source_timestamp: datetime
    collected_at: datetime
    value: Any
    revision: str
    payload_hash: str
    source_url: str | None = None
    market_id: str | None = None
    token_id: str | None = None
    event_id: str | None = None
    confidence: Decimal = Decimal("1")
    model_version: str | None = None

    def __post_init__(self) -> None:
        if not self.source or not self.source_type or not self.revision:
            raise ValueError("source, source_type, and revision are required")
        _require_utc(self.source_timestamp, "source_timestamp")
        _require_utc(self.collected_at, "collected_at")
        if self.collected_at < self.source_timestamp:
            raise ValueError("collected_at cannot precede source_timestamp")
        if not Decimal("0") <= self.confidence <= Decimal("1"):
            raise ValueError("confidence must be between 0 and 1")
        _require_hash(self.payload_hash)


@dataclass(frozen=True, slots=True)
class MarketSnapshot:
    market_id: str
    condition_id: str | None
    question: str
    status: str
    yes_token_id: str | None
    no_token_id: str | None
    source_timestamp: datetime
    collected_at: datetime
    bids: tuple[tuple[Decimal, Decimal], ...]
    asks: tuple[tuple[Decimal, Decimal], ...]
    payload_hash: str
    resolution_rules: str | None = None

    def __post_init__(self) -> None:
        if not self.market_id or not self.question:
            raise ValueError("market_id and question are required")
        _require_utc(self.source_timestamp, "source_timestamp")
        _require_utc(self.collected_at, "collected_at")
        if self.collected_at < self.source_timestamp:
            raise ValueError("collected_at cannot precede source_timestamp")
        _require_hash(self.payload_hash)
        for price, quantity in (*self.bids, *self.asks):
            if not Decimal("0") < price <= Decimal("1") or quantity <= 0:
                raise ValueError("snapshot book levels require probability prices and positive quantities")
