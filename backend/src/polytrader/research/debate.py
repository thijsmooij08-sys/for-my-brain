"""Deterministic, research-only multi-agent debate artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("evaluated_at must include a timezone")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class DebatePosition:
    agent_id: str
    thesis: str
    confidence: Decimal
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.agent_id or not self.thesis:
            raise ValueError("agent and thesis are required")
        if not self.evidence_ids:
            raise ValueError("debate positions require evidence")
        if not Decimal("0") <= self.confidence <= Decimal("1"):
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class DebateArtifact:
    debate_id: str
    topic: str
    consensus: str
    disagreement: Decimal
    positions: tuple[DebatePosition, ...]
    dataset_version: str
    evaluated_at: datetime
    artifact_hash: str
    actionable: bool = False

    def __post_init__(self) -> None:
        if not self.debate_id or not self.topic or not self.consensus or not self.dataset_version:
            raise ValueError("debate identity and provenance are required")
        if not Decimal("0") <= self.disagreement <= Decimal("1"):
            raise ValueError("disagreement must be between 0 and 1")
        _utc(self.evaluated_at)
        if len(self.artifact_hash) != 64:
            raise ValueError("artifact_hash must be SHA-256")
        if self.actionable:
            raise ValueError("research debate artifacts cannot be actionable")


class ResearchDebate:
    """Aggregate independent research positions without producing an order signal."""

    @staticmethod
    def evaluate(
        *, topic: str, positions: tuple[DebatePosition, ...], dataset_version: str,
        evaluated_at: datetime,
    ) -> DebateArtifact:
        if not topic or not dataset_version or not positions:
            raise ValueError("topic, dataset version, and positions are required")
        normalized = tuple(sorted(positions, key=lambda item: (item.thesis, item.agent_id)))
        counts: dict[str, int] = {}
        confidence_totals: dict[str, Decimal] = {}
        for position in normalized:
            counts[position.thesis] = counts.get(position.thesis, 0) + 1
            confidence_totals[position.thesis] = (
                confidence_totals.get(position.thesis, Decimal("0")) + position.confidence
            )
        consensus = max(
            counts,
            key=lambda thesis: (counts[thesis], confidence_totals[thesis], thesis),
        )
        disagreement = Decimal("1") - (Decimal(counts[consensus]) / Decimal(len(normalized)))
        canonical = {
            "topic": topic, "dataset_version": dataset_version,
            "evaluated_at": _utc(evaluated_at).isoformat(),
            "positions": [
                {"agent_id": p.agent_id, "thesis": p.thesis, "confidence": str(p.confidence),
                 "evidence_ids": list(p.evidence_ids)} for p in normalized
            ],
        }
        artifact_hash = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        debate_id = hashlib.sha256(f"{topic}|{dataset_version}|{artifact_hash}".encode()).hexdigest()
        return DebateArtifact(
            debate_id=debate_id, topic=topic, consensus=consensus, disagreement=disagreement,
            positions=normalized, dataset_version=dataset_version,
            evaluated_at=_utc(evaluated_at), artifact_hash=artifact_hash,
        )
