from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Mapping


def _timestamp(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    evidence_id: str
    source: str
    source_timestamp: datetime
    collected_at: datetime
    revision: str
    model_version: str

    def __post_init__(self) -> None:
        if not all((self.evidence_id, self.source, self.revision, self.model_version)):
            raise ValueError("evidence identity and versions are required")
        _timestamp(self.source_timestamp, "source_timestamp")
        _timestamp(self.collected_at, "collected_at")
        if self.collected_at < self.source_timestamp:
            raise ValueError("collected_at cannot precede source_timestamp")


@dataclass(frozen=True, slots=True)
class IntelligenceOutput:
    engine: str
    subject_id: str
    as_of: datetime
    score: Decimal
    confidence: Decimal
    components: Mapping[str, Decimal | str]
    disagreement: Decimal
    evidence: tuple[EvidenceRef, ...]
    model_version: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.engine or not self.subject_id or not self.model_version or not self.evidence:
            raise ValueError("intelligence outputs require identity, version, and evidence")
        _timestamp(self.as_of, "as_of")
        if not Decimal("0") <= self.confidence <= Decimal("1"):
            raise ValueError("confidence must be between zero and one")
        if self.disagreement < 0:
            raise ValueError("disagreement cannot be negative")

    @property
    def actionable(self) -> bool:
        return False
