"""Phase 8 live-readiness contracts with a permanent fail-closed boundary.

This module deliberately contains no SDK secure-client import, signer material,
credential loader, or network submission path. It provides typed contracts and
deterministic checks for a future separately authorized phase.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from polytrader.execution.paper import LiveTradingDisabledError


class SignerUnavailableError(RuntimeError):
    """Raised when a signer is requested while live execution is disabled."""


class LiveSafetyViolation(RuntimeError):
    """Raised when configuration attempts to enable the forbidden live path."""


@dataclass(frozen=True, slots=True)
class LiveSafetyConfig:
    """The authoritative runtime safety policy.

    ``live_trading_enabled`` is intentionally a literal false default. An
    environment value of true is rejected rather than trusted.
    """

    live_trading_enabled: bool = False
    paper_mode: bool = True

    def __post_init__(self) -> None:
        if self.live_trading_enabled:
            raise LiveSafetyViolation("LIVE_TRADING_ENABLED=true is forbidden in Phase 8")
        if not self.paper_mode:
            raise LiveSafetyViolation("Phase 8 requires PAPER mode")

    @classmethod
    def from_environment(cls) -> "LiveSafetyConfig":
        if os.getenv("LIVE_TRADING_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}:
            raise LiveSafetyViolation("LIVE_TRADING_ENABLED must remain false")
        if os.getenv("TRADING_MODE", "PAPER").strip().upper() != "PAPER":
            raise LiveSafetyViolation("TRADING_MODE must remain PAPER")
        return cls()


@dataclass(frozen=True, slots=True)
class AuthenticatedCapability:
    """Redacted description of a future authenticated venue capability."""

    venue: str
    account_id: str
    credential_ref: str | None = None
    signer_available: bool = False

    def __post_init__(self) -> None:
        if self.credential_ref or self.signer_available:
            raise SignerUnavailableError("Authenticated signing is disabled and no secret may be supplied")


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    account_id: str
    cash: Decimal
    equity: Decimal
    positions: Mapping[str, Decimal]
    observed_at: datetime
    source: str
    revision: str

    def __post_init__(self) -> None:
        if self.cash < 0 or self.equity < 0 or any(quantity < 0 for quantity in self.positions.values()):
            raise ValueError("account values and quantities cannot be negative")
        _require_utc(self.observed_at)
        if not self.source or not self.revision:
            raise ValueError("account snapshots require source and revision")


@dataclass(frozen=True, slots=True)
class UserStreamEvent:
    account_id: str
    sequence: int
    event_type: str
    observed_at: datetime
    payload_hash: str

    def __post_init__(self) -> None:
        if self.sequence < 0 or not self.event_type or len(self.payload_hash) != 64:
            raise ValueError("invalid user-stream event")
        _require_utc(self.observed_at)


class UserStreamNormalizer:
    """Normalize only non-secret account-stream metadata."""

    _forbidden = {"secret", "api_key", "api_secret", "private_key", "signature", "passphrase"}

    @classmethod
    def normalize(cls, payload: Mapping[str, Any], *, account_id: str, sequence: int, now: datetime) -> UserStreamEvent:
        if any(key.lower() in cls._forbidden for key in payload):
            raise ValueError("user-stream payload contains forbidden credential material")
        event_type = str(payload.get("type", "unknown"))
        canonical = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return UserStreamEvent(account_id, sequence, event_type, _utc(now), digest)


@dataclass(slots=True)
class SequenceTracker:
    last_sequence: int | None = None
    healthy: bool = True
    reason: str = "not_started"

    def accept(self, event: UserStreamEvent) -> bool:
        if self.last_sequence is not None and event.sequence <= self.last_sequence:
            self.reason = "duplicate_or_replayed"
            return event.sequence == self.last_sequence
        if self.last_sequence is not None and event.sequence != self.last_sequence + 1:
            self.healthy = False
            self.reason = "sequence_gap"
            return False
        self.last_sequence = event.sequence
        self.healthy = True
        self.reason = "ok"
        return True


@dataclass(frozen=True, slots=True)
class ReconciliationResult:
    clean: bool
    reason: str
    checked_at: datetime
    account_revision: str

    def __post_init__(self) -> None:
        _require_utc(self.checked_at)


class Reconciler:
    """Compare local and venue snapshots exactly; uncertainty is dirty."""

    @staticmethod
    def compare(local: AccountSnapshot, venue: AccountSnapshot, *, now: datetime) -> ReconciliationResult:
        checked_at = _utc(now)
        if local.account_id != venue.account_id:
            return ReconciliationResult(False, "account_id_mismatch", checked_at, venue.revision)
        if local.cash != venue.cash or local.equity != venue.equity:
            return ReconciliationResult(False, "cash_or_equity_mismatch", checked_at, venue.revision)
        if dict(local.positions) != dict(venue.positions):
            return ReconciliationResult(False, "position_mismatch", checked_at, venue.revision)
        return ReconciliationResult(True, "reconciled", checked_at, venue.revision)


class ReadinessJournal:
    """Append-only, idempotent audit records for readiness observations."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append_snapshot(self, snapshot: AccountSnapshot) -> bool:
        record = {
            "kind": "account_snapshot",
            "account_id": snapshot.account_id,
            "cash": str(snapshot.cash),
            "equity": str(snapshot.equity),
            "positions": {key: str(value) for key, value in sorted(snapshot.positions.items())},
            "observed_at": snapshot.observed_at.isoformat(),
            "source": snapshot.source,
            "revision": snapshot.revision,
        }
        return self._append(record, f"snapshot:{snapshot.account_id}:{snapshot.revision}")

    def append_reconciliation(self, result: ReconciliationResult) -> bool:
        record = {
            "kind": "reconciliation",
            "clean": result.clean,
            "reason": result.reason,
            "checked_at": result.checked_at.isoformat(),
            "account_revision": result.account_revision,
        }
        return self._append(record, f"reconciliation:{result.account_revision}:{result.checked_at.isoformat()}")

    def _append(self, record: dict[str, object], key: str) -> bool:
        existing = self.path.read_text(encoding="utf-8").splitlines() if self.path.exists() else []
        if any(json.loads(line).get("idempotency_key") == key for line in existing):
            return False
        previous = existing[-1] if existing else ""
        envelope = {"idempotency_key": key, "previous_hash": hashlib.sha256(previous.encode()).hexdigest(), **record}
        payload = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
        envelope["record_hash"] = hashlib.sha256(payload.encode()).hexdigest()
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(envelope, sort_keys=True, separators=(",", ":")) + "\n")
        return True


@dataclass(frozen=True, slots=True)
class EligibilityDecision:
    eligible: bool
    reasons: tuple[str, ...]
    evaluated_at: datetime

    def __post_init__(self) -> None:
        _require_utc(self.evaluated_at)


class EligibilityChecker:
    def evaluate(
        self,
        config: LiveSafetyConfig,
        snapshot: AccountSnapshot | None,
        stream: SequenceTracker,
        reconciliation: ReconciliationResult | None,
        *,
        now: datetime,
        max_snapshot_age: timedelta = timedelta(seconds=60),
    ) -> EligibilityDecision:
        evaluated = _utc(now)
        reasons: list[str] = []
        if not config.live_trading_enabled:
            reasons.append("live_execution_disabled")
        if snapshot is None:
            reasons.append("account_snapshot_missing")
        elif evaluated - snapshot.observed_at > max_snapshot_age:
            reasons.append("account_snapshot_stale")
        if not stream.healthy:
            reasons.append(f"user_stream_{stream.reason}")
        if reconciliation is None or not reconciliation.clean:
            reasons.append("reconciliation_not_clean")
        return EligibilityDecision(not reasons, tuple(reasons), evaluated)


@dataclass(frozen=True, slots=True)
class CircuitBreaker:
    kill_switch: bool = False
    data_healthy: bool = True
    account_reconciled: bool = False
    user_stream_healthy: bool = False

    def tripped(self) -> tuple[str, ...]:
        reasons: list[str] = []
        if self.kill_switch:
            reasons.append("kill_switch")
        if not self.data_healthy:
            reasons.append("data_unhealthy")
        if not self.account_reconciled:
            reasons.append("account_unreconciled")
        if not self.user_stream_healthy:
            reasons.append("user_stream_unhealthy")
        return tuple(reasons)


class LiveExecutionState(StrEnum):
    DISABLED = "DISABLED"
    BLOCKED = "BLOCKED"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"


@dataclass(slots=True)
class LiveExecutionStateMachine:
    config: LiveSafetyConfig = field(default_factory=LiveSafetyConfig)
    state: LiveExecutionState = LiveExecutionState.DISABLED

    def assess(self, eligibility: EligibilityDecision, breaker: CircuitBreaker) -> LiveExecutionState:
        # This phase never reaches an executable state, even with perfect inputs.
        if not self.config.live_trading_enabled:
            self.state = LiveExecutionState.DISABLED
        elif breaker.tripped() or not eligibility.eligible:
            self.state = LiveExecutionState.BLOCKED
        else:
            self.state = LiveExecutionState.READY_FOR_REVIEW
        return self.state

    def submit(self, *_: object, **__: object) -> None:
        raise LiveTradingDisabledError("Live order submission is disabled through Phase 10")


def _utc(value: datetime) -> datetime:
    _require_utc(value)
    return value.astimezone(timezone.utc)


def _require_utc(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
