"""Online SQLite backups with bounded retention and integrity verification."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class BackupResult:
    path: Path
    sha256: str
    bytes: int
    created_at: datetime


def backup_database(
    source: str | Path,
    destination_dir: str | Path,
    *,
    retention: int = 24,
    now: datetime | None = None,
) -> BackupResult:
    """Create an online backup and retain only the newest bounded set."""

    if retention < 1:
        raise ValueError("retention must be positive")
    source_path = Path(source)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    created = now or datetime.now(UTC)
    if created.tzinfo is None or created.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    stamp = created.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = destination / f"polytrader-{stamp}.db"
    if target.exists():
        target = destination / f"polytrader-{stamp}-{created.microsecond:06d}.db"

    source_db = sqlite3.connect(source_path)
    target_db = sqlite3.connect(target)
    try:
        source_db.backup(target_db)
        check = target_db.execute("PRAGMA integrity_check").fetchone()
        if not check or check[0] != "ok":
            raise RuntimeError(f"backup integrity check failed: {check!r}")
    finally:
        target_db.close()
        source_db.close()

    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    result = BackupResult(target, digest, target.stat().st_size, created.astimezone(UTC))
    manifest = destination / "manifest.json"
    entries: list[dict[str, object]] = []
    if manifest.exists():
        try:
            loaded = json.loads(manifest.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                entries = [item for item in loaded if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError):
            entries = []
    entries.append({"path": target.name, "sha256": digest, "bytes": result.bytes,
                    "created_at": result.created_at.isoformat()})
    entries = sorted(entries, key=lambda item: str(item.get("created_at", "")), reverse=True)
    keep = entries[:retention]
    keep_names = {str(item["path"]) for item in keep}
    for candidate in destination.glob("polytrader-*.db"):
        if candidate.name not in keep_names:
            candidate.unlink()
    manifest.write_text(json.dumps(keep, indent=2) + "\n", encoding="utf-8")
    return result
