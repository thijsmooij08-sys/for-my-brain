"""Continuously trigger bounded paper cycles in a fail-closed Docker service."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request


def run_once(api_url: str, limit: int) -> str:
    request = urllib.request.Request(
        f"{api_url.rstrip('/')}/api/v1/paper/cycle?limit={max(1, min(limit, 50))}",
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        return json.dumps({"status": "UNAVAILABLE", "error": str(exc), "live_execution": False})


def main() -> None:
    if os.getenv("PAPER_WORKER_ENABLED", "true").lower() not in {"1", "true", "yes"}:
        print("paper worker disabled", flush=True)
        return
    api_url = os.getenv("PAPER_API_URL", "http://api:8000")
    interval = max(30, int(os.getenv("PAPER_CYCLE_INTERVAL_SECONDS", "300")))
    limit = int(os.getenv("PAPER_MARKET_LIMIT", "20"))
    while True:
        result = run_once(api_url, limit)
        print(result, flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    main()
