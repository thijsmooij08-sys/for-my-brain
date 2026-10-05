from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RolloutRecord:
    version: str
    artifact_hash: str
    status: str
    actionable: bool = False


class PromotionLedger:
    """Append-only Champion/Challenger rollout and rollback history."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def record(self, version: str, artifact_hash: str, status: str) -> RolloutRecord:
        if not version or not artifact_hash or status not in {"ACTIVE", "CANDIDATE", "ROLLBACK"}:
            raise ValueError("invalid rollout record")
        record = RolloutRecord(version, artifact_hash, status, False)
        self._append(record)
        return record

    def rollback(self) -> RolloutRecord:
        records = self.read()
        if len(records) < 2:
            raise ValueError("no prior rollout available for rollback")
        previous = records[-2]
        return self.record(previous.version, previous.artifact_hash, "ROLLBACK")

    def active_version(self) -> str | None:
        active: str | None = None
        for record in self.read():
            if record.status in {"ACTIVE", "ROLLBACK"}:
                active = record.version
        return active

    def read(self) -> tuple[RolloutRecord, ...]:
        if not self.path.exists():
            return ()
        return tuple(RolloutRecord(**json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines())

    def _append(self, record: RolloutRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "version": record.version, "artifact_hash": record.artifact_hash,
                "status": record.status, "actionable": False,
            }, sort_keys=True) + "\n")
