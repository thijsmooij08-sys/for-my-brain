import sqlite3
from datetime import UTC, datetime

from polytrader.maintenance.backup import backup_database


def test_backup_is_integrity_checked_and_retained(tmp_path) -> None:
    source = tmp_path / "source.db"
    with sqlite3.connect(source) as db:
        db.execute("create table evidence (id integer primary key, value text)")
        db.execute("insert into evidence(value) values ('book')")
    backups = tmp_path / "backups"
    first = backup_database(source, backups, retention=1, now=datetime(2026, 1, 1, tzinfo=UTC))
    second = backup_database(source, backups, retention=1, now=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC))
    assert first.path.exists() is False
    assert second.path.exists() is True
    assert len(list(backups.glob("polytrader-*.db"))) == 1
    assert len(second.sha256) == 64
    with sqlite3.connect(second.path) as db:
        assert db.execute("pragma integrity_check").fetchone()[0] == "ok"
        assert db.execute("select count(*) from evidence").fetchone()[0] == 1
