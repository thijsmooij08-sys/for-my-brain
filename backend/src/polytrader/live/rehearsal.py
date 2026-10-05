"""Redacted account/reconciliation rehearsal for Phase 9 operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Mapping

from polytrader.live.readiness import AccountSnapshot, Reconciler, ReconciliationResult


@dataclass(frozen=True, slots=True)
class RehearsalFixture:
    account_id: str
    cash: str
    equity: str
    positions: Mapping[str, str]
    revision: str
    observed_at: datetime

    def snapshot(self) -> AccountSnapshot:
        return AccountSnapshot(
            account_id=self.account_id,
            cash=Decimal(self.cash),
            equity=Decimal(self.equity),
            positions={key: Decimal(value) for key, value in self.positions.items()},
            observed_at=self.observed_at,
            source="redacted-rehearsal",
            revision=self.revision,
        )


def run_reconciliation_rehearsal(
    local: RehearsalFixture,
    venue: RehearsalFixture,
    *,
    now: datetime,
) -> ReconciliationResult:
    """Compare two redacted snapshots using the production exact-Decimal path."""
    return Reconciler.compare(local.snapshot(), venue.snapshot(), now=now)
