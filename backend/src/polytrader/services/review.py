from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
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


@dataclass(frozen=True, slots=True)
class TradeJournalSummary:
    cycle_count: int
    completed_count: int
    eligibility_rate: Decimal
    buy_count: int
    sell_count: int
    actionable: bool = False

    def __post_init__(self) -> None:
        if self.cycle_count < 0 or self.completed_count < 0:
            raise ValueError("journal counts cannot be negative")
        if not Decimal("0") <= self.eligibility_rate <= Decimal("1"):
            raise ValueError("eligibility rate must be between 0 and 1")
        if self.actionable:
            raise ValueError("journal summaries cannot be actionable")


class TradeJournalAnalyzer:
    """Summarize paper-cycle outcomes without creating strategy or order authority."""

    def analyze(self, records: tuple[ReviewRecord, ...]) -> TradeJournalSummary:
        scanned = sum(record.scanned for record in records)
        eligible = sum(record.eligible for record in records)
        if scanned < 0 or eligible < 0:
            raise ValueError("journal inputs cannot contain negative counts")
        rate = Decimal(eligible) / Decimal(scanned) if scanned else Decimal("0")
        return TradeJournalSummary(
            cycle_count=len(records),
            completed_count=sum(record.status == "COMPLETED" for record in records),
            eligibility_rate=rate,
            buy_count=sum(record.buys for record in records),
            sell_count=sum(record.sells for record in records),
        )
