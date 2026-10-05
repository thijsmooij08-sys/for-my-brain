from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol

from polytrader.domain.market import OrderBook
from polytrader.integrations.polymarket.adapter import MarketSummary
from polytrader.market_data.health import DataHealthMonitor
from polytrader.risk.manager import RiskManager
from polytrader.services.review import PaperReviewJournal, ReviewRecord
from polytrader.services.trading import PaperTradingService
from polytrader.sizing.sizer import PositionSizer
from polytrader.strategies.development import DevelopmentStrategy, Signal


class PaperMarketSource(Protocol):
    async def list_markets(self, limit: int = 20) -> list[MarketSummary]: ...
    async def order_book(self, token_id: str) -> OrderBook: ...


@dataclass(frozen=True, slots=True)
class PaperCycleReport:
    cycle_id: str
    status: str
    scanned: int
    eligible: int
    buy_count: int
    sell_count: int
    rejected: int
    reviewed: int
    reasons: tuple[str, ...]


class AutonomousPaperTrader:
    """One idempotent, observable paper-only SCAN→REVIEW cycle."""

    def __init__(self, *, source: PaperMarketSource, strategy: DevelopmentStrategy,
                 sizer: PositionSizer, risk: RiskManager, service: PaperTradingService,
                 journal: PaperReviewJournal | None = None,
                 health: DataHealthMonitor | None = None) -> None:
        self.source, self.strategy, self.sizer, self.risk, self.service = source, strategy, sizer, risk, service
        self.journal = journal
        self.health = health or DataHealthMonitor(max_age_seconds=risk.config.max_data_age_seconds)
        self._completed_cycles: set[str] = set()

    async def run_cycle(self, observed_at: datetime, *, limit: int = 20) -> PaperCycleReport:
        markets = await self.source.list_markets(limit)
        cycle_id = f"paper:{observed_at.isoformat()}:{limit}"
        journal_has_cycle = self.journal is not None and any(
            record.cycle_id == cycle_id for record in self.journal.read()
        )
        if cycle_id in self._completed_cycles or journal_has_cycle:
            return PaperCycleReport(cycle_id, "DUPLICATE", len(markets), 0, 0, 0, 0, 0, ("cycle already completed",))
        if self.risk.config.kill_switch:
            self._completed_cycles.add(cycle_id)
            return PaperCycleReport(cycle_id, "KILLED", len(markets), 0, 0, 0, 0, 0, ("kill switch enabled",))
        eligible = 0
        buys = 0
        sells = 0
        rejected = 0
        reasons: list[str] = []
        candidates: list[tuple[MarketSummary, OrderBook, Signal, str]] = []
        for market in markets:
            normalized_status = market.status.lower()
            simple_open_state = normalized_status in {"active", "open"}
            sdk_open_state = "active=true" in normalized_status and "accepting_orders=true" in normalized_status
            if not (simple_open_state or sdk_open_state) or not market.yes_token_id:
                reasons.append(f"{market.market_id}:ineligible-lifecycle")
                continue
            book = await self.source.order_book(market.yes_token_id)
            if not book.bids or not book.asks:
                reasons.append(f"{market.market_id}:incomplete-book")
                continue
            if book.source_timestamp is None:
                reasons.append(f"{market.market_id}:missing-source-timestamp")
                continue
            health = self.health.evaluate(book.source_timestamp, observed_at)
            if not health.can_open_exposure:
                reasons.append(f"{market.market_id}:data-{health.status.value}")
                continue
            eligible += 1
            signal = self.strategy.analyze(market.market_id, market.yes_token_id, book, observed_at)
            if signal.action != "BUY":
                reasons.append(f"{market.market_id}:no-action")
                continue
            assert market.yes_token_id is not None
            candidates.append((market, book, signal, market.yes_token_id))
        candidates.sort(key=lambda item: item[2].fair_probability - (item[1].best_ask() or Decimal("1")), reverse=True)
        for market, book, _signal, token_id in candidates:
            result = self.service_workflow(book, market.market_id, observed_at)
            if result.fill is not None and result.fill.filled_quantity > 0:
                buys += 1
            elif result.risk is not None and not result.risk.approved:
                rejected += 1
                reasons.append(f"{market.market_id}:{result.risk.reason_code}")
            position = self.service.engine.positions().get(token_id)
            if position and position[0] > 0:
                average_cost = position[1] / position[0]
                best_bid = book.best_bid()
                if best_bid is not None and best_bid >= average_cost * Decimal("1.05"):
                    exit_result = self._exit(market.market_id, book, observed_at, position[0])
                    if exit_result is not None and exit_result.filled_quantity > 0:
                        sells += 1
        self._completed_cycles.add(cycle_id)
        report = PaperCycleReport(cycle_id, "COMPLETED", len(markets), eligible, buys, sells, rejected, eligible, tuple(reasons))
        if self.journal is not None:
            self.journal.append(ReviewRecord(cycle_id, report.status, report.scanned, report.eligible,
                                              report.buy_count, report.sell_count, report.reasons))
        return report

    def service_workflow(self, book: OrderBook, market_id: str, observed_at: datetime):
        from polytrader.services.trading import PaperTradingWorkflow
        return PaperTradingWorkflow(self.strategy, self.sizer, self.risk, self.service).run(market_id, book, observed_at)

    def _exit(self, market_id: str, book: OrderBook, observed_at: datetime, quantity: Decimal):
        from polytrader.opportunities.engine import OpportunityEngine
        from polytrader.orders.intent import OrderIntent
        opportunity = OpportunityEngine().from_exit(market_id, book.token_id, book, observed_at)
        spread = book.spread()
        liquidity = sum((level.quantity for level in book.bids), Decimal("0"))
        decision = self.risk.evaluate(
            opportunity.action_id, Decimal("0"), spread if spread is not None else Decimal("1"), observed_at,
            current_total_exposure=self.service.engine.total_exposure(),
            current_market_exposure=self.service.engine.market_exposure(book.token_id), liquidity=liquidity,
        )
        if not decision.approved:
            return None
        intent = OrderIntent.from_approved(opportunity, quantity, decision)
        return self.service.execute(intent, book)
