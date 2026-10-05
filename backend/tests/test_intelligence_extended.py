from datetime import UTC, datetime
from decimal import Decimal

from polytrader.intelligence.extended import (
    EarningsIntelligenceEngine,
    FundamentalIntelligenceEngine,
    IncomeFactorEngine,
    MacroRegimeEngine,
    PatternDiscoveryEngine,
    PeerIntelligenceEngine,
    ResearchClaim,
)
from polytrader.intelligence.models import EvidenceRef


def ref() -> EvidenceRef:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return EvidenceRef("e", "source", now, now, "v1", "model.v1")


def test_extended_engines_remain_research_only() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    claim = ResearchClaim("quality", Decimal("0.8"), ref())
    assert FundamentalIntelligenceEngine().evaluate("x", (claim,), as_of=now).actionable is False
    assert EarningsIntelligenceEngine().surprise("x", actual=Decimal("110"), expected=Decimal("100"), as_of=now, evidence=(ref(),)).score == Decimal("0.1")
    assert PeerIntelligenceEngine().compare("x", {"peer": Decimal("0.7")}, as_of=now, evidence=(ref(),)).score == Decimal("0.7")
    assert MacroRegimeEngine().classify("x", {"growth": Decimal("0.1")}, as_of=now, evidence=(ref(),)).components["regime"] == "risk_on"
    assert IncomeFactorEngine().score("x", dividend_yield=Decimal("0.04"), payout_stability=Decimal("0.8"), as_of=now, evidence=(ref(),)).score == Decimal("0.032")
    report = PatternDiscoveryEngine().evaluate("test", effect_size=Decimal("0.1"), p_values={"h": Decimal("0.01")}, sample_size=100)
    assert report.status == "RESEARCH_ONLY"
