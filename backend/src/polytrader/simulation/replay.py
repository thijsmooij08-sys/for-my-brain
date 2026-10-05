from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Callable


def _utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    return value.astimezone(UTC)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return _utc(value, "datetime").isoformat()
    if isinstance(value, Mapping):
        return {str(k): _json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class ReplayEvent:
    event_id: str
    sequence: int
    source_timestamp: datetime
    collected_at: datetime
    token_id: str
    kind: str
    payload: Mapping[str, Any]
    payload_hash: str

    def __post_init__(self) -> None:
        if not self.event_id or self.sequence < 0 or not self.token_id or not self.kind:
            raise ValueError("replay event identity and sequence are required")
        _utc(self.source_timestamp, "source_timestamp")
        _utc(self.collected_at, "collected_at")
        if self.collected_at < self.source_timestamp:
            raise ValueError("collected_at cannot precede source_timestamp")
        if len(self.payload_hash) != 64 or any(char not in "0123456789abcdef" for char in self.payload_hash):
            raise ValueError("payload_hash must be a lowercase SHA-256 hex digest")

    def canonical(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id, "sequence": self.sequence,
            "source_timestamp": _utc(self.source_timestamp, "source_timestamp").isoformat(),
            "collected_at": _utc(self.collected_at, "collected_at").isoformat(),
            "token_id": self.token_id, "kind": self.kind,
            "payload": _json_value(self.payload), "payload_hash": self.payload_hash,
        }


@dataclass(frozen=True, slots=True)
class DatasetManifest:
    dataset_id: str
    content_hash: str
    created_at: datetime
    source: str
    event_count: int
    start_timestamp: datetime
    end_timestamp: datetime
    schema_version: str = "phase3.v1"

    def __post_init__(self) -> None:
        _utc(self.created_at, "created_at")
        _utc(self.start_timestamp, "start_timestamp")
        _utc(self.end_timestamp, "end_timestamp")
        if self.end_timestamp < self.start_timestamp or self.event_count < 1:
            raise ValueError("manifest range and event count are invalid")
        if self.dataset_id != self.content_hash[:16]:
            raise ValueError("dataset_id must be the content hash prefix")

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id, "content_hash": self.content_hash,
            "created_at": _utc(self.created_at, "created_at").isoformat(), "source": self.source,
            "event_count": self.event_count,
            "start_timestamp": _utc(self.start_timestamp, "start_timestamp").isoformat(),
            "end_timestamp": _utc(self.end_timestamp, "end_timestamp").isoformat(),
            "schema_version": self.schema_version,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> DatasetManifest:
        return cls(
            dataset_id=str(value["dataset_id"]), content_hash=str(value["content_hash"]),
            created_at=datetime.fromisoformat(str(value["created_at"])), source=str(value["source"]),
            event_count=int(value["event_count"]),
            start_timestamp=datetime.fromisoformat(str(value["start_timestamp"])),
            end_timestamp=datetime.fromisoformat(str(value["end_timestamp"])),
            schema_version=str(value.get("schema_version", "phase3.v1")),
        )


@dataclass(frozen=True, slots=True)
class ReplayDataset:
    events: tuple[ReplayEvent, ...]
    manifest: DatasetManifest

    @classmethod
    def from_events(cls, events: Iterable[ReplayEvent], *, source: str = "polytrader.evidence",
                    created_at: datetime | None = None) -> ReplayDataset:
        ordered = tuple(sorted(events, key=lambda event: (event.source_timestamp, event.sequence, event.event_id)))
        if not ordered:
            raise ValueError("a replay dataset requires at least one event")
        sequences = [event.sequence for event in ordered]
        if len(set(sequences)) != len(sequences):
            raise ValueError("replay event sequences must be unique")
        encoded = json.dumps([event.canonical() for event in ordered], sort_keys=True, separators=(",", ":"))
        content_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        created = _utc(created_at or datetime.now(UTC), "created_at")
        manifest = DatasetManifest(
            dataset_id=content_hash[:16], content_hash=content_hash, created_at=created,
            source=source, event_count=len(ordered),
            start_timestamp=_utc(ordered[0].source_timestamp, "source_timestamp"),
            end_timestamp=_utc(ordered[-1].source_timestamp, "source_timestamp"),
        )
        return cls(ordered, manifest)

    def until(self, timestamp: datetime) -> Iterator[ReplayEvent]:
        cutoff = _utc(timestamp, "timestamp")
        return (event for event in self.events if _utc(event.source_timestamp, "source_timestamp") <= cutoff)


class ReplayClock:
    def __init__(self, start: datetime) -> None:
        self.current = _utc(start, "start")

    def advance_to(self, timestamp: datetime) -> datetime:
        target = _utc(timestamp, "timestamp")
        if target < self.current:
            raise ValueError("replay clock cannot move backwards")
        self.current = target
        return self.current


@dataclass(frozen=True, slots=True)
class ReplaySummary:
    dataset_id: str
    event_count: int
    start_timestamp: datetime
    end_timestamp: datetime


class ReplayRunner:
    """Replay immutable evidence in deterministic point-in-time order."""

    def __init__(self, dataset: ReplayDataset) -> None:
        self.dataset = dataset

    def run(self, handler: Callable[[ReplayEvent, ReplayClock], None]) -> ReplaySummary:
        clock = ReplayClock(self.dataset.events[0].source_timestamp)
        for event in self.dataset.events:
            clock.advance_to(event.source_timestamp)
            handler(event, clock)
        return ReplaySummary(
            dataset_id=self.dataset.manifest.dataset_id, event_count=len(self.dataset.events),
            start_timestamp=self.dataset.events[0].source_timestamp,
            end_timestamp=self.dataset.events[-1].source_timestamp,
        )
