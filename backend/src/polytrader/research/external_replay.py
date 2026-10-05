"""Safe importer for reviewed external replay snapshots.

The input format is deliberately boring: one canonical ``ReplayEvent`` JSON
object per line. This keeps imports auditable and prevents third-party code
from entering the PolyTrader runtime.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from polytrader.research.external_catalog import ExternalResearchCatalog
from polytrader.simulation.replay import ReplayDataset, ReplayEvent


@dataclass(frozen=True, slots=True)
class ExternalReplayDataset:
    dataset: ReplayDataset
    source_id: str
    license_ref: str
    input_sha256: str


def _reject_binary_floats(value: Any) -> None:
    if isinstance(value, float):
        raise ValueError("numeric payload values must be decimal strings")
    if isinstance(value, Mapping):
        for nested in value.values():
            _reject_binary_floats(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            _reject_binary_floats(nested)


def _parse_timestamp(value: Any) -> datetime:
    timestamp = datetime.fromisoformat(str(value))
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return timestamp.astimezone(UTC)


class ExternalReplayImporter:
    """Convert reviewed JSONL snapshots into immutable research replay data."""

    def __init__(self, catalog: ExternalResearchCatalog | None = None) -> None:
        self.catalog = catalog or ExternalResearchCatalog.default()

    def from_jsonl(
        self, path: Path, *, source_id: str, license_ref: str
    ) -> ExternalReplayDataset:
        source = self.catalog.require(source_id)
        if not source.research_only:
            raise ValueError(f"source {source_id!r} is not approved for research import")
        if not license_ref.strip():
            raise ValueError("license_ref is required")

        raw = path.read_bytes()
        if not raw.strip():
            raise ValueError("external replay input is empty")
        events: list[ReplayEvent] = []
        seen_sequences: set[int] = set()
        previous_timestamp: datetime | None = None
        for line_number, line in enumerate(raw.splitlines(), start=1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}") from exc
            if not isinstance(value, Mapping):
                raise ValueError(f"event on line {line_number} must be an object")
            payload = value.get("payload")
            if not isinstance(payload, Mapping):
                raise ValueError(f"payload on line {line_number} must be an object")
            _reject_binary_floats(payload)
            try:
                source_timestamp = _parse_timestamp(value["source_timestamp"])
                collected_at = _parse_timestamp(value["collected_at"])
            except ValueError:
                raise
            try:
                sequence = int(value["sequence"])
                payload_hash = str(value["payload_hash"])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"invalid event fields on line {line_number}") from exc
            if previous_timestamp is not None and source_timestamp < previous_timestamp:
                raise ValueError("source timestamp regression in external replay")
            previous_timestamp = source_timestamp
            if sequence in seen_sequences:
                raise ValueError(f"duplicate replay sequence {sequence}")
            seen_sequences.add(sequence)
            canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            expected_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()
            if payload_hash != expected_hash:
                raise ValueError(f"payload hash mismatch on line {line_number}")
            events.append(
                ReplayEvent(
                    event_id=str(value["event_id"]), sequence=sequence,
                    source_timestamp=source_timestamp, collected_at=collected_at,
                    token_id=str(value["token_id"]), kind=str(value["kind"]),
                    payload=dict(payload), payload_hash=payload_hash,
                )
            )
        return ExternalReplayDataset(
            dataset=ReplayDataset.from_events(events, source=f"external:{source_id}"),
            source_id=source_id, license_ref=license_ref, input_sha256=hashlib.sha256(raw).hexdigest(),
        )
