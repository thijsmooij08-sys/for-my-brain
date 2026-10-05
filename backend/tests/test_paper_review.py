from pathlib import Path

from polytrader.services.review import PaperReviewJournal, ReviewRecord


def test_review_journal_is_append_only_and_idempotent(tmp_path: Path) -> None:
    journal = PaperReviewJournal(tmp_path / "reviews.jsonl")
    record = ReviewRecord("cycle-1", "COMPLETED", 2, 1, 1, 0, ("ok",))
    journal.append(record)
    journal.append(record)
    assert journal.read() == (record,)
