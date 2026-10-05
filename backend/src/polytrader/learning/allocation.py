"""Research-only strategy allocation proposals with hard safety boundaries."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AllocationProposal:
    strategy_id: str
    requested_weight: Decimal
    closed_samples: int
    net_realized_pnl: Decimal
    max_drawdown: Decimal


@dataclass(frozen=True, slots=True)
class AllocationDecision:
    strategy_id: str
    approved_weight: Decimal
    approved: bool
    reasons: tuple[str, ...]
    execution_authority: bool = False


@dataclass(frozen=True, slots=True)
class AllocationRecord:
    strategy_id: str
    approved_weight: Decimal
    approved: bool
    reasons: tuple[str, ...]
    observed_at: datetime
    record_hash: str


class ResearchAllocator:
    """Suggest bounded weights; never changes RiskManager or capital limits."""

    def __init__(
        self,
        *,
        minimum_samples: int = 30,
        maximum_weight: Decimal = Decimal("0.25"),
        maximum_drawdown: Decimal = Decimal("0.05"),
    ) -> None:
        if minimum_samples <= 0 or not Decimal("0") <= maximum_weight <= Decimal("1"):
            raise ValueError("invalid allocation limits")
        if not Decimal("0") <= maximum_drawdown <= Decimal("1"):
            raise ValueError("invalid drawdown limit")
        self.minimum_samples = minimum_samples
        self.maximum_weight = maximum_weight
        self.maximum_drawdown = maximum_drawdown

    def propose(self, proposal: AllocationProposal) -> AllocationDecision:
        reasons: list[str] = []
        if not proposal.strategy_id:
            reasons.append("strategy_id_missing")
        if proposal.requested_weight < 0:
            reasons.append("negative_weight")
        if proposal.closed_samples < self.minimum_samples:
            reasons.append("insufficient_samples")
        if proposal.net_realized_pnl <= 0:
            reasons.append("non_positive_net_pnl")
        if proposal.max_drawdown > self.maximum_drawdown:
            reasons.append("drawdown_limit")
        weight = min(max(proposal.requested_weight, Decimal("0")), self.maximum_weight)
        if reasons:
            weight = Decimal("0")
        return AllocationDecision(proposal.strategy_id, weight, not reasons, tuple(reasons))


class AllocationLedger:
    """Append-only, hash-chained audit trail for research allocation decisions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, decision: AllocationDecision, *, observed_at: datetime) -> AllocationRecord:
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("allocation timestamps must be timezone-aware")
        existing = self.path.read_text(encoding="utf-8").splitlines() if self.path.exists() else []
        previous_hash = json.loads(existing[-1])["record_hash"] if existing else ""
        payload = {
            "strategy_id": decision.strategy_id,
            "approved_weight": str(decision.approved_weight),
            "approved": decision.approved,
            "reasons": list(decision.reasons),
            "execution_authority": False,
            "observed_at": observed_at.isoformat(),
            "previous_hash": previous_hash,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        record_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps({**payload, "record_hash": record_hash}, sort_keys=True) + "\n")
        return AllocationRecord(
            decision.strategy_id, decision.approved_weight, decision.approved,
            decision.reasons, observed_at, record_hash,
        )

    def read(self) -> tuple[dict[str, object], ...]:
        if not self.path.exists():
            return ()
        return tuple(json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines())
