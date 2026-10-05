"""Read one public Polymarket market-stream event without credentials."""

import asyncio
import sys

from polymarket.clients import AsyncPublicClient
from polymarket.streams import MarketSpec


async def main() -> int:
    token_id = sys.argv[1] if len(sys.argv) > 1 else "32338220190071351435772801779725302244575775216413325951443816017994629993401"
    async with AsyncPublicClient() as client:
        handle = await client.subscribe(MarketSpec(token_ids=[token_id], custom_feature_enabled=True))
        try:
            event = await asyncio.wait_for(handle.__anext__(), timeout=20)
            print(f"stream_event_type={getattr(event, 'type', type(event).__name__)}")
            return 0
        finally:
            await handle.close()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
