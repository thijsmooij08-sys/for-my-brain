"""Read-only research data adapters with provenance and point-in-time metadata.

These adapters never create trading clients, hold wallet material, or emit
signals. They return canonical evidence observations for the research plane.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx

from polytrader.evidence.models import EvidenceObservation


class ReadOnlyIntegrationError(RuntimeError):
    """Raised when an optional public integration is unavailable or unconfigured."""


def _hash_payload(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _timestamp(value: Any, fallback: datetime) -> datetime:
    if not value:
        return fallback
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return fallback
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


@dataclass(slots=True)
class ReadOnlyJsonClient:
    base_url: str
    source: str
    transport: httpx.AsyncBaseTransport | None = None

    async def get_json(self, path: str, params: dict[str, str] | None = None, headers: dict[str, str] | None = None) -> EvidenceObservation:
        collected = datetime.now(UTC)
        async with httpx.AsyncClient(base_url=self.base_url, transport=self.transport, timeout=20.0) as client:
            response = await client.get(path, params=params, headers=headers)
            response.raise_for_status()
            payload = response.json()
        source_timestamp = _timestamp(
            payload.get("updated_at") if isinstance(payload, dict) else None, collected
        )
        if source_timestamp > collected:
            raise ReadOnlyIntegrationError("source timestamp is in the future")
        return EvidenceObservation(
            source=self.source,
            source_type="public_json",
            source_timestamp=source_timestamp,
            collected_at=collected,
            value=payload,
            revision=str(payload.get("revision", payload.get("updated_at", "unknown")))
            if isinstance(payload, dict) else "unknown",
            payload_hash=_hash_payload(payload),
            source_url=str(response.url),
        )


class PolymarketDataApiV2Client(ReadOnlyJsonClient):
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        super().__init__("https://data-api.polymarket.com", "polymarket-data-api-v2", transport)

    async def market_state(self, market_id: str) -> EvidenceObservation:
        return await self.get_json(f"/v2/markets/{market_id}")

    async def prices_history(
        self,
        token_id: str,
        *,
        start: int | None = None,
        end: int | None = None,
        interval: str | None = None,
        limit: int | None = None,
    ) -> EvidenceObservation:
        """Fetch the public, point-in-time price series for one outcome token."""
        params = {"token_id": token_id}
        if start is not None:
            params["start"] = str(start)
        if end is not None:
            params["end"] = str(end)
        if interval is not None:
            params["interval"] = interval
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get_json("/v2/prices-history", params=params)


class SecEdgarClient(ReadOnlyJsonClient):
    def __init__(self, user_agent: str | None = None, transport: httpx.AsyncBaseTransport | None = None) -> None:
        agent = user_agent or os.getenv("POLYTRADER_SEC_USER_AGENT", "").strip()
        if not agent:
            raise ReadOnlyIntegrationError("POLYTRADER_SEC_USER_AGENT is required for SEC requests")
        super().__init__("https://data.sec.gov", "sec-edgar-xbrl", transport)
        self.user_agent = agent

    async def company_facts(self, cik: str) -> EvidenceObservation:
        normalized = str(cik).zfill(10)
        return await self.get_json(f"/api/xbrl/companyfacts/CIK{normalized}.json", headers={"User-Agent": self.user_agent})


class NasdaqDataLinkClient(ReadOnlyJsonClient):
    def __init__(self, api_key: str | None = None, transport: httpx.AsyncBaseTransport | None = None) -> None:
        super().__init__("https://data.nasdaq.com", "nasdaq-data-link", transport)
        self.api_key = api_key or os.getenv("NASDAQ_DATA_LINK_API_KEY", "").strip()

    async def dataset(self, code: str) -> EvidenceObservation:
        params = {"api_key": self.api_key} if self.api_key else None
        return await self.get_json(f"/api/v3/datasets/{code}.json", params=params)


@dataclass(frozen=True, slots=True)
class OpenBBResearchDescriptor:
    """Metadata for the isolated OpenBB environment; not an execution adapter."""

    package: str = "openbb"
    version: str = "5.0.0"
    execution_authority: bool = False
    isolation: str = "backend/.openbb-venv"
