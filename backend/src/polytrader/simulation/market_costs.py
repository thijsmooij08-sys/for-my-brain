"""Research-only Polymarket cost and settlement timing models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


def _utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class PolymarketFeeModel:
    """Price-sensitive V2 taker fee estimate; makers are exempt."""

    fee_rate: Decimal

    def __post_init__(self) -> None:
        if not Decimal("0") <= self.fee_rate <= Decimal("1"):
            raise ValueError("fee_rate must be between zero and one")

    def fee(self, notional: Decimal, price: Decimal, *, role: str = "TAKER") -> Decimal:
        if notional < 0 or not Decimal("0") <= price <= Decimal("1"):
            raise ValueError("notional must be non-negative and price must be between zero and one")
        normalized_role = role.upper()
        if normalized_role not in {"TAKER", "MAKER"}:
            raise ValueError("role must be TAKER or MAKER")
        if normalized_role == "MAKER":
            return Decimal("0")
        return notional * self.fee_rate * price * (Decimal("1") - price)


@dataclass(frozen=True, slots=True)
class ResolutionSchedule:
    """Settlement timing metadata used to measure capital lock-up in research."""

    market_id: str
    resolution_at: datetime
    settlement_at: datetime
    disputed: bool = False

    def __post_init__(self) -> None:
        if not self.market_id:
            raise ValueError("market_id is required")
        resolution = _utc(self.resolution_at, "resolution_at")
        settlement = _utc(self.settlement_at, "settlement_at")
        if settlement < resolution:
            raise ValueError("settlement_at cannot precede resolution_at")

    @property
    def capital_locked_until(self) -> datetime:
        return _utc(self.settlement_at, "settlement_at")

    def is_locked(self, at: datetime) -> bool:
        return _utc(at, "at") < self.capital_locked_until
