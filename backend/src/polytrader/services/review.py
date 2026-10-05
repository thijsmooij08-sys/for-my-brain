from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ReviewRecord:
    cycle_id: str
    status: str
    scanned: int
    eligible: int
    buys: int
    sells: int
    reasons: tuple[str, ...]


class PaperReviewJournal:
    """Append-only paper-cycle review artifacts with cycle idempotency."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: ReviewRecord) -> None:
        if record.cycle_id in {item.cycle_id for item in self.read()}:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(record), sort_keys=True) + "\n")

    def read(self) -> tuple[ReviewRecord, ...]:
        if not self.path.exists():
            return ()
        records: list[ReviewRecord] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            value = json.loads(line)
            value["reasons"] = tuple(value["reasons"])
            records.append(ReviewRecord(**value))
        return tuple(records)
