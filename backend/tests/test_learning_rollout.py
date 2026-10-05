from polytrader.learning.rollout import PromotionLedger


def test_promotion_ledger_supports_explicit_rollback(tmp_path) -> None:
    ledger = PromotionLedger(tmp_path / "rollouts.jsonl")
    ledger.record("1", "hash-1", "ACTIVE")
    ledger.record("2", "hash-2", "ACTIVE")
    rollback = ledger.rollback()
    assert rollback.version == "1"
    assert rollback.status == "ROLLBACK"
    assert ledger.active_version() == "1"
    assert all(item.actionable is False for item in ledger.read())
