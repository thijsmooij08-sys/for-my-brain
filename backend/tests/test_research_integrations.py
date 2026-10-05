import asyncio

import httpx
import pytest

from polytrader.providers.research import (
    NasdaqDataLinkClient,
    OpenBBResearchDescriptor,
    PolymarketDataApiV2Client,
    ReadOnlyIntegrationError,
    SecEdgarClient,
)


def transport(payload: dict[str, object]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, request=request)
    return httpx.MockTransport(handler)


def test_public_adapters_return_hashed_evidence_without_authentication() -> None:
    observation = asyncio.run(PolymarketDataApiV2Client(transport=transport({"updated_at": "2026-10-05T00:00:00Z", "data": []})).market_state("m1"))
    assert observation.source == "polymarket-data-api-v2"
    assert len(observation.payload_hash) == 64
    assert observation.collected_at >= observation.source_timestamp


def test_polymarket_prices_history_uses_public_token_id_window() -> None:
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen.update(dict(request.url.params))
        return httpx.Response(200, json={"updated_at": "2026-10-05T00:00:00Z", "data": []}, request=request)

    asyncio.run(PolymarketDataApiV2Client(transport=httpx.MockTransport(handler)).prices_history(
        "token-1", start=100, end=200, interval="1d", limit=10,
    ))
    assert seen == {"token_id": "token-1", "start": "100", "end": "200", "interval": "1d", "limit": "10"}


def test_sec_nasdaq_adapters_keep_credentials_out_of_evidence() -> None:
    payload = {"updated_at": "2026-10-05T00:00:00Z", "observations": []}
    sec = SecEdgarClient(user_agent="PolyTrader research contact", transport=transport(payload))
    nasdaq = NasdaqDataLinkClient(api_key="test-key", transport=transport(payload))
    sec_record, nasdaq_record = asyncio.run(_fetch_records(sec, nasdaq))
    for record in (sec_record, nasdaq_record):
        assert "test-key" not in str(record.value)
        assert "User-Agent" not in str(record.value)


async def _fetch_records(sec: SecEdgarClient, nasdaq: NasdaqDataLinkClient):
    return await asyncio.gather(
        sec.company_facts("1234"), nasdaq.dataset("TEST/DATA")
    )


def test_required_credentials_fail_closed_and_openbb_is_research_only(monkeypatch) -> None:
    monkeypatch.delenv("POLYTRADER_SEC_USER_AGENT", raising=False)
    with pytest.raises(ReadOnlyIntegrationError):
        SecEdgarClient()
    descriptor = OpenBBResearchDescriptor()
    assert descriptor.execution_authority is False
    assert descriptor.isolation.endswith(".openbb-venv")
