from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class RiskConfig:
    max_order_notional: Decimal = Decimal("100")
    max_spread: Decimal = Decimal("0.05")
    max_data_age_seconds: int = 60
    kill_switch: bool = False
    max_total_exposure: Decimal = Decimal("1000")
    max_market_exposure: Decimal = Decimal("250")
    minimum_liquidity: Decimal = Decimal("0")
    daily_loss_limit: Decimal = Decimal("100")


@dataclass(frozen=True, slots=True)
class RiskDecision:
    approved: bool
    reason_code: str
    human_reason: str


class RiskManager:
    def __init__(self, config: RiskConfig) -> None:
        self.config, self._seen_actions = config, set()

    def evaluate(
        self, action_id: str, notional: Decimal, spread: Decimal, data_at: datetime,
        current_total_exposure: Decimal = Decimal("0"), current_market_exposure: Decimal = Decimal("0"),
        liquidity: Decimal | None = None, realized_daily_loss: Decimal = Decimal("0"),
    ) -> RiskDecision:
        now = datetime.now(UTC)
        if self.config.kill_switch:
            return RiskDecision(False, "KILL_SWITCH", "Manual kill switch is enabled")
        if action_id in self._seen_actions:
            return RiskDecision(False, "DUPLICATE_ACTION", "Action was already evaluated")
        if now - data_at > timedelta(seconds=self.config.max_data_age_seconds):
            return RiskDecision(False, "DATA_STALE", "Market data is stale")
        if notional > self.config.max_order_notional:
            return RiskDecision(False, "MAX_ORDER_NOTIONAL", "Order exceeds hard limit")
        if current_total_exposure + notional > self.config.max_total_exposure:
            return RiskDecision(False, "MAX_TOTAL_EXPOSURE", "Order exceeds total exposure limit")
        if current_market_exposure + notional > self.config.max_market_exposure:
            return RiskDecision(False, "MAX_MARKET_EXPOSURE", "Order exceeds market exposure limit")
        if self.config.minimum_liquidity > 0 and (liquidity is None or liquidity < self.config.minimum_liquidity):
            return RiskDecision(False, "INSUFFICIENT_LIQUIDITY", "Market liquidity is below requirement")
        if realized_daily_loss >= self.config.daily_loss_limit:
            return RiskDecision(False, "DAILY_LOSS_LIMIT", "Daily loss protection is active")
        if spread > self.config.max_spread:
            return RiskDecision(False, "SPREAD_TOO_WIDE", "Spread exceeds configured limit")
        self._seen_actions.add(action_id)
        return RiskDecision(True, "APPROVED", "Within deterministic Phase 1 limits")
