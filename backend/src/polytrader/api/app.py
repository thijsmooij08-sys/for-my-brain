import os
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, generate_latest
from pydantic import BaseModel

from polytrader.execution.paper import PaperExecutionEngine
from polytrader.integrations.polymarket.adapter import PolymarketPublicAdapter
from polytrader.learning.allocation import AllocationLedger, AllocationProposal, ResearchAllocator
from polytrader.live.authorization import ActivationRequest, LimitedLiveGate
from polytrader.live.preflight import OperationalPreflight
from polytrader.live.readiness import (
    CircuitBreaker,
    EligibilityChecker,
    LiveExecutionStateMachine,
    LiveSafetyConfig,
    SequenceTracker,
)
from polytrader.market_data.health import DataHealthMonitor
from polytrader.persistence.repository import PortfolioRepository
from polytrader.risk.manager import RiskConfig, RiskManager
from polytrader.services.paper_loop import AutonomousPaperTrader
from polytrader.services.trading import PaperTradingService
from polytrader.sizing.sizer import PositionSizer
from polytrader.strategies.development import DevelopmentStrategy

app = FastAPI(title="PolyTrader", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=[],
)
_default_database = (Path(__file__).resolve().parents[4] / "backend" / "polytrader.db").as_posix()
_repository = PortfolioRepository(
    os.getenv("POLYTRADER_DATABASE_URL", f"sqlite:///{_default_database}")
)
_data_health = DataHealthMonitor(max_age_seconds=60)
_api_requests = Counter("polytrader_api_requests_total", "API requests served", ["route"])
_live_execution = Gauge("polytrader_live_execution_enabled", "Live execution safety switch (always zero)")
_trading_mode = Gauge("polytrader_trading_mode", "Active trading mode", ["mode"])
_paper_cash = Gauge("polytrader_paper_cash", "Paper account cash balance")
_paper_equity = Gauge("polytrader_paper_equity", "Paper account equity")
_paper_realized_pnl = Gauge("polytrader_paper_realized_pnl", "Paper account realized P&L")
_paper_fill_count = Gauge("polytrader_paper_fill_count", "Paper fills recorded")
_paper_win_rate = Gauge("polytrader_paper_win_rate_percent", "Paper closed-trade win rate percent")
_live_execution.set(0)
_trading_mode.labels("PAPER").set(1)
_live_safety = LiveSafetyConfig.from_environment()
_live_state_machine = LiveExecutionStateMachine(_live_safety)
_paper_risk = RiskManager(RiskConfig(max_order_notional=Decimal("10"), max_total_exposure=Decimal("100")))
_paper_engine = PaperExecutionEngine(Decimal("10000"))
_paper_state = _repository.state(Decimal("10000"))
_paper_engine.restore(
    cash=_paper_state["cash"],
    positions={
        token_id: (item["quantity"], item["cost_basis"])
        for token_id, item in _paper_state["positions"].items()
    },
)
_paper_trader = AutonomousPaperTrader(
    source=PolymarketPublicAdapter(),
    strategy=DevelopmentStrategy(Decimal("0.55")),
    sizer=PositionSizer(Decimal("10")),
    risk=_paper_risk,
    service=PaperTradingService(_paper_engine, _repository),
)
_research_allocator = ResearchAllocator()
_allocation_ledger = AllocationLedger(
    os.getenv(
        "POLYTRADER_ALLOCATION_LEDGER",
        str(Path(__file__).resolve().parents[4] / "backend" / ".runtime" / "allocation.jsonl"),
    )
)


class AllocationRequestModel(BaseModel):
    strategy_id: str
    requested_weight: Decimal
    closed_samples: int
    net_realized_pnl: Decimal
    max_drawdown: Decimal


@app.get("/api/v1/health")
def health() -> dict[str, object]:
    _api_requests.labels("health").inc()
    return {"status": "ok", "trading_mode": "PAPER", "live_execution": False}


@app.get("/metrics")
def metrics() -> Response:
    state = _repository.state(Decimal("10000.00"))
    _paper_cash.set(float(state["cash"]))
    _paper_equity.set(float(state["equity"]))
    _paper_realized_pnl.set(float(state["realized_pnl"]))
    _paper_fill_count.set(len(state["orders"]))
    _paper_win_rate.set(float(_repository.paper_performance(Decimal("10000.00"))["win_rate"]))
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/system")
def system() -> dict[str, object]:
    return {"mode": "PAPER", "kill_switch": False, "live_execution": False}


@app.get("/api/v1/live-readiness")
def live_readiness() -> dict[str, object]:
    """Expose redacted readiness diagnostics; never exposes credentials or enables execution."""
    stream = SequenceTracker()
    decision = EligibilityChecker().evaluate(
        _live_safety,
        None,
        stream,
        None,
        now=datetime.now(timezone.utc),
    )
    state = _live_state_machine.assess(
        decision,
        CircuitBreaker(account_reconciled=False, user_stream_healthy=False),
    )
    return {
        "state": state.value,
        "eligible": decision.eligible,
        "reasons": list(decision.reasons),
        "live_execution": False,
        "credentials_loaded": False,
        "signer_available": False,
    }


@app.get("/api/v1/live-preflight")
def live_preflight() -> dict[str, object]:
    """Expose redacted Phase 9 preflight checks; activation always remains denied."""
    now = datetime.now(timezone.utc)
    stream = SequenceTracker()
    eligibility = EligibilityChecker().evaluate(
        _live_safety, None, stream, None, now=now,
    )
    breaker = CircuitBreaker(account_reconciled=False, user_stream_healthy=False)
    activation = LimitedLiveGate().evaluate(
        _live_safety,
        ActivationRequest("api-preflight", False, now),
        eligibility,
    )
    report = OperationalPreflight().evaluate(
        _live_safety, eligibility, breaker,
        data_health=False, journal_integrity=True, activation=activation,
    )
    paper_state = _repository.state(Decimal("10000"))
    return {
        "activation_allowed": report.activation_allowed,
        "checks": [asdict(check) for check in report.checks],
        "reasons": list(activation.reasons),
        "live_execution": False,
        "paper_operational": True,
        "paper_account": {
            "cash": str(paper_state["cash"]),
            "equity": str(paper_state["equity"]),
            "open_positions": len(paper_state["positions"]),
            "fills": len(paper_state["orders"]),
        },
    }


@app.get("/api/v1/data-health")
def data_health() -> dict[str, object]:
    status = _data_health.disconnected("no ingestion has run")
    return {
        "status": status.status.value,
        "checked_at": status.checked_at.isoformat(),
        "last_source_timestamp": None,
        "reason": status.reason,
        "can_open_exposure": status.can_open_exposure,
    }


@app.get("/api/v1/portfolio")
def portfolio() -> dict[str, object]:
    state = _repository.state(Decimal("10000.00"))
    return {
        "trading_mode": "PAPER", "cash": str(state["cash"]), "equity": str(state["equity"]),
        "realized_pnl": str(state["realized_pnl"]),
    }


@app.get("/api/v1/paper/performance")
def paper_performance() -> dict[str, object]:
    performance = _repository.paper_performance(Decimal("10000.00"))
    return {key: (str(value) if isinstance(value, Decimal) else value) for key, value in performance.items()}


@app.get("/api/v1/learning/status")
def learning_status() -> dict[str, object]:
    return {
        "mode": "RESEARCH_ONLY",
        "allocation_authority": False,
        "risk_bypass": False,
        "live_execution": False,
    }


@app.post("/api/v1/learning/allocation")
def propose_learning_allocation(request: AllocationRequestModel) -> dict[str, object]:
    """Record a bounded research proposal; it cannot authorize or place orders."""
    decision = _research_allocator.propose(AllocationProposal(
        request.strategy_id, request.requested_weight, request.closed_samples,
        request.net_realized_pnl, request.max_drawdown,
    ))
    record = _allocation_ledger.append(decision, observed_at=datetime.now(timezone.utc))
    return {
        "strategy_id": decision.strategy_id,
        "approved": decision.approved,
        "approved_weight": str(decision.approved_weight),
        "reasons": list(decision.reasons),
        "execution_authority": False,
        "live_execution": False,
        "record_hash": record.record_hash,
    }


@app.post("/api/v1/paper/cycle")
async def run_paper_cycle(limit: int = 20) -> dict[str, object]:
    """Run one bounded public-data paper cycle; never submits a venue order."""
    report = await _paper_trader.run_cycle(datetime.now(timezone.utc), limit=max(1, min(limit, 50)))
    return {**asdict(report), "live_execution": False}


@app.get("/api/v1/positions")
def positions() -> dict[str, list[object]]:
    state = _repository.state(Decimal("10000.00"))
    return {"items": [
        {"token_id": token_id, "quantity": str(item["quantity"]), "cost_basis": str(item["cost_basis"])}
        for token_id, item in state["positions"].items()
    ]}


@app.get("/api/v1/orders")
def orders() -> dict[str, list[object]]:
    return {"items": _repository.state(Decimal("10000.00"))["orders"]}


@app.get("/api/v1/markets")
async def markets(limit: int = 20) -> dict[str, list[dict[str, object]]]:
    items = await PolymarketPublicAdapter().list_markets(limit)
    return {
        "items": [
            {
                "market_id": market.market_id,
                "condition_id": market.condition_id,
                "question": market.question,
                "status": market.status,
            }
            for market in items
        ]
    }
