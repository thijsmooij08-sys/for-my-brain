from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polytrader.intelligence.events import EventObservation, EventStudyEngine
from polytrader.intelligence.graph import MarketEventGraph
from polytrader.intelligence.models import EvidenceRef, IntelligenceOutput
from polytrader.intelligence.technical import TechnicalFeatureEngine, TimedPrice


def _evidence(name: str = "ev-1") -> EvidenceRef:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    return EvidenceRef(name, "polymarket", now, now, "v1", "model.v1")


def test_intelligence_output_keeps_evidence_and_cannot_be_actionable() -> None:
    output = IntelligenceOutput(
        engine="technical", subject_id="yes", as_of=datetime(2026, 1, 1, tzinfo=UTC),
        score=Decimal("0.25"), confidence=Decimal("0.80"), components={"momentum": "0.25"},
        disagreement=Decimal("0.10"), evidence=(_evidence(),), model_version="technical.v1",
        limitations=("research-only",),
    )
    assert output.evidence[0].evidence_id == "ev-1"
    assert output.actionable is False


def test_technical_engine_is_point_in_time_and_exact_decimal() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    points = tuple(TimedPrice(base + timedelta(minutes=i), Decimal(value), (_evidence(f"ev-{i}"),))
                   for i, value in enumerate(("0.40", "0.50", "0.60")))
    feature = TechnicalFeatureEngine().compute("yes", points, as_of=base + timedelta(minutes=1))
    assert feature.components["momentum"] == Decimal("0.25")
    assert feature.as_of == base + timedelta(minutes=1)


def test_event_study_rejects_future_event_data_and_computes_forward_move() -> None:
    base = datetime(2026, 1, 1, tzinfo=UTC)
    events = (EventObservation("evt", base, _evidence()),)
    prices = ((base, Decimal("0.50")), (base + timedelta(hours=1), Decimal("0.60")))
    result = EventStudyEngine().run(events, prices)
    assert result.sample_size == 1
    assert result.average_forward_return == Decimal("0.20")
    with pytest.raises(ValueError):
        EventStudyEngine().run((EventObservation("evt", base + timedelta(hours=2), _evidence()),), prices)


def test_market_event_graph_preserves_asset_boundaries() -> None:
    graph = MarketEventGraph()
    graph.add_market("m1", "polymarket")
    graph.add_event("e1", "resolution")
    graph.link("m1", "e1", "resolves_by")
    assert graph.neighbors("m1") == (("e1", "resolves_by"),)
