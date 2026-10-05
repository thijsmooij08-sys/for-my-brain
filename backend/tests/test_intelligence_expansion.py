from datetime import UTC, datetime
from decimal import Decimal

from polytrader.intelligence.fusion import SignalFusionEngine
from polytrader.intelligence.models import EvidenceRef
from polytrader.intelligence.valuation import ValuationEngine, ValuationScenario


def evidence() -> EvidenceRef:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return EvidenceRef("ev-valuation", "research", now, now, "v1", "valuation.v1")


def test_valuation_engine_preserves_bear_base_bull_assumptions() -> None:
    engine = ValuationEngine()
    result = engine.evaluate(
        "asset-1",
        scenarios=(
            ValuationScenario("bear", Decimal("0.20"), evidence()),
            ValuationScenario("base", Decimal("0.50"), evidence()),
            ValuationScenario("bull", Decimal("0.80"), evidence()),
        ),
        as_of=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert result.components["bear"] == Decimal("0.20")
    assert result.components["bull"] == Decimal("0.80")
    assert result.actionable is False


def test_signal_fusion_retains_disagreement_and_evidence() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    refs = (evidence(),)
    result = SignalFusionEngine().fuse(
        "asset-1", now,
        (("technical", Decimal("0.80"), refs), ("event", Decimal("0.20"), refs)),
    )
    assert result.score == Decimal("0.50")
    assert result.disagreement == Decimal("0.60")
    assert len(result.evidence) == 1
    assert result.actionable is False
