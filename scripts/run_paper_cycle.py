"""Run one public-data autonomous paper cycle.

This command is intentionally bounded to one cycle by default. It uses the
existing Strategy -> Opportunity -> Sizing -> Risk -> Paper Execution path;
it never imports a secure client or submits a venue order.
"""

from __future__ import annotations

import argparse
import asyncio
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from polytrader.execution.paper import PaperExecutionEngine
from polytrader.integrations.polymarket.adapter import PolymarketPublicAdapter
from polytrader.persistence.repository import PortfolioRepository
from polytrader.risk.manager import RiskConfig, RiskManager
from polytrader.services.paper_loop import AutonomousPaperTrader
from polytrader.services.review import PaperReviewJournal
from polytrader.services.trading import PaperTradingService
from polytrader.sizing.sizer import PositionSizer
from polytrader.strategies.development import DevelopmentStrategy


async def main(limit: int) -> None:
    database_url = os.getenv("POLYTRADER_DATABASE_URL", "sqlite:///backend/polytrader.db")
    repository = PortfolioRepository(database_url)
    if repository.fills():
        raise SystemExit("Refusing to start with existing fills until engine-state restoration is enabled")
    risk = RiskManager(RiskConfig(max_order_notional=Decimal(10), max_total_exposure=Decimal(100)))
    trader = AutonomousPaperTrader(
        source=PolymarketPublicAdapter(),
        strategy=DevelopmentStrategy(Decimal("0.55")),
        sizer=PositionSizer(Decimal(10)),
        risk=risk,
        service=PaperTradingService(PaperExecutionEngine(Decimal(10000)), repository),
        journal=PaperReviewJournal(Path("backend/.runtime/paper-review.jsonl")),
    )
    report = await trader.run_cycle(datetime.now(UTC), limit=limit)
    print({
        "status": report.status,
        "cycle_id": report.cycle_id,
        "scanned": report.scanned,
        "eligible": report.eligible,
        "paper_buys": report.buy_count,
        "paper_sells": report.sell_count,
        "risk_rejections": report.rejected,
        "live_execution": False,
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    asyncio.run(main(args.limit))
