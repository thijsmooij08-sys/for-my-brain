"""Periodic local backup worker for the paper ledger and evidence database."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from polytrader.maintenance.backup import backup_database

log = logging.getLogger("polytrader.backup")


def main() -> None:
    if os.getenv("BACKUP_WORKER_ENABLED", "true").lower() not in {"1", "true", "yes"}:
        log.info("backup worker disabled")
        return
    source = Path(os.getenv("POLYTRADER_DATABASE_PATH", "/data/polytrader.db"))
    destination = Path(os.getenv("POLYTRADER_BACKUP_DIR", "/backups"))
    interval = max(60, int(os.getenv("POLYTRADER_BACKUP_INTERVAL_SECONDS", "3600")))
    retention = max(1, int(os.getenv("POLYTRADER_BACKUP_RETENTION", "24")))
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    while True:
        try:
            result = backup_database(source, destination, retention=retention)
            log.info("backup_created path=%s bytes=%d sha256=%s", result.path, result.bytes, result.sha256)
        except Exception:
            log.exception("backup failed; retrying on next interval")
        time.sleep(interval)


if __name__ == "__main__":
    main()
