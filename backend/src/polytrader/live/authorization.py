"""Explicit limited-live preparation gates; activation remains impossible."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from polytrader.live.readiness import EligibilityDecision, LiveSafetyConfig


@dataclass(frozen=True, slots=True)
class ActivationRequest:
    """Auditable operator intent without credentials or signing material."""

    change_ticket: str
    operator_acknowledged: bool
    requested_at: datetime

    def __post_init__(self) -> None:
        if not self.change_ticket or len(self.change_ticket) > 120:
            raise ValueError("a bounded change ticket is required")
        if self.requested_at.tzinfo is None or self.requested_at.utcoffset() is None:
            raise ValueError("activation timestamps must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ActivationDecision:
    allowed: bool
    reasons: tuple[str, ...]


class LimitedLiveGate:
    """Evaluate future operator intent while the repository policy is disabled."""

    def evaluate(
        self,
        config: LiveSafetyConfig,
        request: ActivationRequest,
        eligibility: EligibilityDecision | None,
    ) -> ActivationDecision:
        reasons: list[str] = []
        if not config.live_trading_enabled:
            reasons.append("repository_live_policy_disabled")
        if not request.operator_acknowledged:
            reasons.append("operator_acknowledgement_missing")
        if eligibility is None or not eligibility.eligible:
            reasons.append("preflight_not_eligible")
        # This explicit final denial is intentional until a separately
        # authorized future policy changes the repository safety boundary.
        if "live_activation_authorized" not in reasons:
            reasons.append("activation_requires_separate_authorization")
        return ActivationDecision(False, tuple(reasons))
