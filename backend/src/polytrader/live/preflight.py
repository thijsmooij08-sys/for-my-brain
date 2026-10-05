"""Deterministic operational preflight for future limited-live review."""

from __future__ import annotations

from dataclasses import dataclass

from polytrader.live.authorization import ActivationDecision
from polytrader.live.readiness import CircuitBreaker, EligibilityDecision, LiveSafetyConfig


@dataclass(frozen=True, slots=True)
class PreflightCheck:
    name: str
    passed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class PreflightReport:
    checks: tuple[PreflightCheck, ...]
    activation_allowed: bool


class OperationalPreflight:
    """Produce redacted checks; never converts a safe system into live mode."""

    def evaluate(
        self,
        config: LiveSafetyConfig,
        eligibility: EligibilityDecision | None,
        breaker: CircuitBreaker,
        *,
        data_health: bool,
        journal_integrity: bool,
        activation: ActivationDecision,
    ) -> PreflightReport:
        checks = (
            PreflightCheck("policy_locked_off", not config.live_trading_enabled, "live policy remains disabled"),
            PreflightCheck("paper_mode", config.paper_mode, "PAPER mode is required"),
            PreflightCheck("data_health", data_health, "public data health gate"),
            PreflightCheck("account_eligibility", eligibility is not None and eligibility.eligible, "account preflight"),
            PreflightCheck("circuit_breakers", not breaker.tripped(), "all deterministic breakers clear"),
            PreflightCheck("journal_integrity", journal_integrity, "readiness journal integrity"),
            PreflightCheck("activation_authorized", activation.allowed, "separate authorization gate"),
        )
        # The explicit policy is the final authority; this remains false in
        # every Phase 9 runtime regardless of other check values.
        return PreflightReport(checks, False)
