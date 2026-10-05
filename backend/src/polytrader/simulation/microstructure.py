"""Conservative, research-only microstructure estimates."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class QueueFillEstimate:
    requested_quantity: Decimal
    queue_ahead: Decimal
    traded_volume: Decimal
    filled_quantity: Decimal
    remaining_quantity: Decimal
    queue_remaining: Decimal
    actionable: bool = False


class ConservativeQueueModel:
    """Estimate resting-order fills only after modeled queue volume is consumed."""

    @staticmethod
    def estimate(
        *, requested_quantity: Decimal, queue_ahead: Decimal, traded_volume: Decimal
    ) -> QueueFillEstimate:
        if requested_quantity <= 0:
            raise ValueError("requested_quantity must be positive")
        if queue_ahead < 0 or traded_volume < 0:
            raise ValueError("queue_ahead and traded_volume cannot be negative")
        available = max(Decimal("0"), traded_volume - queue_ahead)
        filled = min(requested_quantity, available)
        return QueueFillEstimate(
            requested_quantity=requested_quantity, queue_ahead=queue_ahead,
            traded_volume=traded_volume, filled_quantity=filled,
            remaining_quantity=requested_quantity - filled,
            queue_remaining=max(Decimal("0"), queue_ahead - traded_volume),
        )
