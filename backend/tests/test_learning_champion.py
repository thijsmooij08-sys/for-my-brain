from decimal import Decimal

from polytrader.learning.champion import CandidateEvaluation, ChampionChallengerPolicy


def test_challenger_requires_evidence_and_material_improvement() -> None:
    policy = ChampionChallengerPolicy(min_samples=10, min_improvement=Decimal("0.02"))
    champion = CandidateEvaluation("champion", "1", Decimal("0.60"), 20, "hash-c")
    challenger = CandidateEvaluation("challenger", "2", Decimal("0.64"), 20, "hash-n")
    decision = policy.compare(champion, challenger)
    assert decision.promote is True
    assert decision.selected_version == "2"
    assert decision.actionable is False


def test_challenger_is_rejected_when_evidence_is_insufficient() -> None:
    policy = ChampionChallengerPolicy(min_samples=10, min_improvement=Decimal("0.01"))
    champion = CandidateEvaluation("champion", "1", Decimal("0.60"), 20, "hash-c")
    challenger = CandidateEvaluation("challenger", "2", Decimal("0.80"), 9, "hash-n")
    decision = policy.compare(champion, challenger)
    assert decision.promote is False
    assert decision.reason == "INSUFFICIENT_EVIDENCE"
