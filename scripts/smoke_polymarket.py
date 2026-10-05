"""Read-only live smoke test for the official public Polymarket SDK."""
import asyncio

from polymarket import AsyncPublicClient


async def main() -> None:
    async with AsyncPublicClient() as client:
        page = await client.list_markets(page_size=1).first_page()
        if not page.items:
            raise RuntimeError("official SDK returned no public markets")
        market = page.items[0]
        print(f"market_id={market.id} question={market.question}")
        token_ids = getattr(market, "clob_token_ids", None) or getattr(market, "tokens", None)
        if token_ids is None:
            token_ids = (market.outcomes.yes, market.outcomes.no)
        if not token_ids:
            raise RuntimeError("market did not expose outcome/token information")
        first_token = token_ids[0]
        token_id = getattr(first_token, "token_id", None) or getattr(first_token, "asset_id", None) or first_token
        book = await client.get_order_book(token_id=token_id)
        print(f"token_id={token_id} bids={len(book.bids)} asks={len(book.asks)}")


asyncio.run(main())
