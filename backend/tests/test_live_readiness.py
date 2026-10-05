from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polytrader.execution.paper import LiveTradingDisabledError
from polytrader.live.authorization import ActivationDecision, ActivationRequest, LimitedLiveGate
from polytrader.live.preflight import OperationalPreflight
from polytrader.live.readiness import (
    AccountSnapshot,
    AuthenticatedCapability,
    CircuitBreaker,
    EligibilityChecker,
    LiveExecutionState,
    LiveExecutionStateMachine,
    LiveSafetyConfig,
    LiveSafetyViolation,
    ReadinessJournal,
    Reconciler,
    SequenceTracker,
    SignerUnavailableError,
    UserStreamNormalizer,
)
from polytrader.live.rehearsal import RehearsalFixture, run_reconciliation_rehearsal

NOW = datetime(2026, 10, 5, 0, 0, tzinfo=timezone.utc)


def snapshot(*, cash: str = "100", revision: str = "r1", observed_at: datetime = NOW) -> AccountSnapshot:
    return AccountSnapshot("acct", Decimal(cash), Decimal(cash), {"token": Decimal("2")}, observed_at, "test", revision)


def test_phase8_safety_rejects_true_live_configuration_and_signer_material(monkeypatch) -> None:
    with pytest.raises(LiveSafetyViolation):
        LiveSafetyConfig(live_trading_enabled=True)
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "true")
    with pytest.raises(LiveSafetyViolation):
        LiveSafetyConfig.from_environment()
    with pytest.raises(SignerUnavailableError):
        AuthenticatedCapability("polymarket", "acct", credential_ref="secret-ref")


def test_phase9_limited_live_gate_remains_denied_without_execution_authority() -> None:
    request = ActivationRequest("change-123", True, NOW)
    decision = LimitedLiveGate().evaluate(LiveSafetyConfig(), request, None)
    assert decision.allowed is False
    assert "repository_live_policy_disabled" in decision.reasons
    assert "activation_requires_separate_authorization" in decision.reasons


def test_phase9_preflight_reports_checks_but_never_allows_activation() -> None:
    activation = LimitedLiveGate().evaluate(
        LiveSafetyConfig(), ActivationRequest("change-123", True, NOW), None,
    )
    report = OperationalPreflight().evaluate(
        LiveSafetyConfig(), None,
        CircuitBreaker(account_reconciled=False, user_stream_healthy=False),
        data_health=False, journal_integrity=True, activation=activation,
    )
    assert report.activation_allowed is False
    assert {check.name for check in report.checks} == {
        "policy_locked_off", "paper_mode", "data_health", "account_eligibility",
        "circuit_breakers", "journal_integrity", "activation_authorized",
    }


def test_phase9_redacted_reconciliation_rehearsal_is_exact_and_fail_closed() -> None:
    local = RehearsalFixture("acct", "100.00", "101.25", {"token": "2.5"}, "r1", NOW)
    clean = run_reconciliation_rehearsal(local, local, now=NOW)
    dirty = run_reconciliation_rehearsal(
        local,
        RehearsalFixture("acct", "100.01", "101.25", {"token": "2.5"}, "r2", NOW),
        now=NOW,
    )
    assert clean.clean is True
    assert dirty.clean is False
    assert dirty.reason == "cash_or_equity_mismatch"


def test_phase9_adversarial_gate_denies_even_when_inputs_claim_success() -> None:
    request = ActivationRequest("change-123", True, NOW)
    gate = LimitedLiveGate()
    denied = gate.evaluate(LiveSafetyConfig(), request, None)
    assert denied.allowed is False
    # The preflight layer cannot be tricked by a fabricated positive decision.
    report = OperationalPreflight().evaluate(
        LiveSafetyConfig(), None,
        CircuitBreaker(), data_health=True, journal_integrity=True,
        activation=ActivationDecision(True, ()),
    )
    assert report.activation_allowed is False


def test_phase9_operator_request_rejects_invalid_timestamp_and_unbounded_ticket() -> None:
    with pytest.raises(ValueError, match="timezone"):
        ActivationRequest("change-123", True, datetime(2026, 10, 5, 0, 0))
    with pytest.raises(ValueError, match="bounded"):
        ActivationRequest("x" * 121, True, NOW)


def test_user_stream_hashes_metadata_and_detects_gap() -> None:
    tracker = SequenceTracker()
    first = UserStreamNormalizer.normalize({"type": "balance", "cash": "100"}, account_id="acct", sequence=1, now=NOW)
    second = UserStreamNormalizer.normalize({"type": "position"}, account_id="acct", sequence=3, now=NOW)
    assert tracker.accept(first)
    assert not tracker.accept(second)
    assert not tracker.healthy
    assert len(first.payload_hash) == 64


def test_reconciliation_is_exact_and_fail_closed() -> None:
    result = Reconciler.compare(snapshot(), snapshot(), now=NOW)
    assert result.clean
    dirty = Reconciler.compare(snapshot(), snapshot(cash="100.01"), now=NOW)
    assert not dirty.clean
    assert dirty.reason == "cash_or_equity_mismatch"


def test_readiness_journal_is_append_only_and_idempotent(tmp_path) -> None:
    journal = ReadinessJournal(tmp_path / "readiness.jsonl")
    item = snapshot()
    assert journal.append_snapshot(item)
    assert not journal.append_snapshot(item)
    result = Reconciler.compare(item, item, now=NOW)
    assert journal.append_reconciliation(result)
    lines = (tmp_path / "readiness.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert all("record_hash" in line and "private_key" not in line for line in lines)


def test_eligibility_and_state_machine_never_become_executable() -> None:
    stream = SequenceTracker()
    reconciliation = Reconciler.compare(snapshot(), snapshot(), now=NOW)
    decision = EligibilityChecker().evaluate(LiveSafetyConfig(), snapshot(), stream, reconciliation, now=NOW)
    assert not decision.eligible
    assert "live_execution_disabled" in decision.reasons
    machine = LiveExecutionStateMachine()
    state = machine.assess(decision, CircuitBreaker(account_reconciled=True, user_stream_healthy=True))
    assert state is LiveExecutionState.DISABLED
    with pytest.raises(LiveTradingDisabledError):
        machine.submit("intent")


def test_stale_account_and_secret_fields_are_rejected() -> None:
    stale = AccountSnapshot("acct", Decimal("1"), Decimal("1"), {}, NOW - timedelta(minutes=2), "test", "r")
    decision = EligibilityChecker().evaluate(
        LiveSafetyConfig(), stale, SequenceTracker(), None, now=NOW
    )
    assert "account_snapshot_stale" in decision.reasons
    with pytest.raises(ValueError):
        UserStreamNormalizer.normalize({"type": "balance", "private_key": "x"}, account_id="acct", sequence=1, now=NOW)
