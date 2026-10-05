from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol

from polytrader.domain.market import BookLevel, OrderBook
from polytrader.evidence.models import EvidenceObservation
from polytrader.market_data.health import DataHealthMonitor, DataHealthStatus
from polytrader.persistence.repository import PortfolioRepository


@dataclass(frozen=True, slots=True)
class MarketLifecycle:
    market_id: str
    status: str
    source_timestamp: datetime


@dataclass(frozen=True, slots=True)
class MarketEventEvidence:
    """A public stream event that does not mutate the local order book."""

    event_type: str
    token_id: str | None
    value: dict[str, Any]
    source_timestamp: datetime


class EventStreamFactory(Protocol):
    def __call__(self) -> AsyncIterator[Any]: ...


class OrderBookStore:
    """Maintain books from authoritative snapshots and incremental changes."""

    def __init__(self) -> None:
        self._books: dict[str, OrderBook] = {}
        self._lifecycle: dict[str, MarketLifecycle] = {}

    def get(self, token_id: str) -> OrderBook | None:
        return self._books.get(token_id)

    def lifecycle(self, market_id: str) -> MarketLifecycle | None:
        return self._lifecycle.get(market_id)

    def apply(self, event: Any, *, received_at: datetime | None = None) -> OrderBook | MarketLifecycle | MarketEventEvidence | None:
        received = received_at or datetime.now(UTC)
        event_type = _event_type(event)
        payload = _payload(event)
        timestamp = _timestamp(payload) or received
        if event_type == "book":
            token_id = _text(payload, "asset_id", "token_id")
            bids = _levels(payload, "bids", reverse=True)
            asks = _levels(payload, "asks", reverse=False)
            book = OrderBook(token_id, bids, asks, source_timestamp=timestamp, received_at=received)
            self._books[token_id] = book
            return book
        if event_type == "price_change":
            latest: OrderBook | None = None
            for change in _items(payload, "price_changes"):
                token_id = _text(change, "asset_id", "token_id")
                current = self._books.get(token_id)
                if current is None:
                    continue
                side = _text(change, "side").upper()
                price = Decimal(str(_value(change, "price")))
                size = Decimal(str(_value(change, "size")))
                levels = dict((level.price, level.quantity) for level in (current.bids if side == "BUY" else current.asks))
                if size <= 0:
                    levels.pop(price, None)
                else:
                    levels[price] = size
                bids = tuple(BookLevel(p, q) for p, q in sorted(
                    ((p, q) for p, q in levels.items()) if side == "BUY" else
                    ((level.price, level.quantity) for level in current.bids),
                    key=lambda pair: pair[0], reverse=True))
                asks = tuple(BookLevel(p, q) for p, q in sorted(
                    ((p, q) for p, q in levels.items()) if side != "BUY" else
                    ((level.price, level.quantity) for level in current.asks),
                    key=lambda pair: pair[0]))
                book = OrderBook(token_id, bids, asks, source_timestamp=timestamp, received_at=received)
                self._books[token_id] = book
                latest = book
            return latest
        if event_type in {"market_resolved", "new_market"}:
            market_id = _text(payload, "condition_id", "market", "id")
            status = "resolved" if event_type == "market_resolved" else "active"
            lifecycle = MarketLifecycle(market_id, status, timestamp)
            self._lifecycle[market_id] = lifecycle
            return lifecycle
        if event_type in {"last_trade_price", "tick_size_change", "best_bid_ask"}:
            token_id = _optional_text(payload, "asset_id", "token_id")
            value = _public_event_value(event_type, payload, token_id)
            return MarketEventEvidence(event_type, token_id, value, timestamp)
        return None


class ReconnectingMarketStream:
    """Consume a public stream and reconnect with bounded exponential backoff."""

    def __init__(self, factory: EventStreamFactory, *, max_reconnects: int = 3,
                 backoff_seconds: float = 0.25, sleep: Callable[[float], Any] | None = None) -> None:
        self.factory = factory
        self.max_reconnects = max_reconnects
        self.backoff_seconds = backoff_seconds
        self.sleep = sleep or asyncio.sleep

    async def events(self) -> AsyncIterator[Any]:
        reconnects = 0
        while True:
            try:
                async for event in self.factory():
                    reconnects = 0
                    yield event
                return
            except asyncio.CancelledError:
                raise
            except Exception:
                if reconnects >= self.max_reconnects:
                    raise
                await self.sleep(self.backoff_seconds * (2**reconnects))
                reconnects += 1


class StreamingIngestionService:
    """Apply public events, persist point-in-time evidence, and expose health."""

    def __init__(self, stream: ReconnectingMarketStream, repository: PortfolioRepository,
                 store: OrderBookStore | None = None, clock: Callable[[], datetime] | None = None,
                 health: DataHealthMonitor | None = None) -> None:
        self.stream = stream
        self.repository = repository
        self.store = store or OrderBookStore()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.health = health or DataHealthMonitor(60)
        self._health_status: DataHealthStatus | None = None

    @property
    def health_status(self) -> DataHealthStatus | None:
        return self._health_status

    async def run(self, *, max_events: int | None = None) -> int:
        count = 0
        async for event in self.stream.events():
            received = self.clock()
            result = self.store.apply(event, received_at=received)
            source_timestamp = getattr(result, "source_timestamp", None)
            if source_timestamp is not None:
                self._health_status = self.health.evaluate(source_timestamp, now=received)
            if isinstance(result, OrderBook):
                value = {"token_id": result.token_id, "bids": [[str(x.price), str(x.quantity)] for x in result.bids],
                         "asks": [[str(x.price), str(x.quantity)] for x in result.asks]}
                self.repository.record_evidence(EvidenceObservation(
                    source="polymarket", source_type="public_market_stream",
                    source_timestamp=result.source_timestamp or received, collected_at=received,
                    value=value, revision="stream", payload_hash=_hash(value), token_id=result.token_id))
            elif isinstance(result, MarketLifecycle):
                value = {"market_id": result.market_id, "status": result.status}
                self.repository.record_evidence(EvidenceObservation(
                    source="polymarket", source_type="public_market_lifecycle",
                    source_timestamp=result.source_timestamp, collected_at=received,
                    value=value, revision="lifecycle", payload_hash=_hash(value), market_id=result.market_id))
            elif isinstance(result, MarketEventEvidence):
                self.repository.record_evidence(EvidenceObservation(
                    source="polymarket", source_type=f"public_market_{result.event_type}",
                    source_timestamp=result.source_timestamp, collected_at=received,
                    value=result.value, revision="stream", payload_hash=_hash(result.value),
                    token_id=result.token_id))
            count += 1
            if max_events is not None and count >= max_events:
                break
        return count


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _value(obj: Any, key: str) -> Any:
    return getattr(obj, key) if hasattr(obj, key) else obj[key]


def _text(obj: Any, *keys: str) -> str:
    for key in keys:
        try:
            value = _value(obj, key)
        except (KeyError, AttributeError):
            continue
        if value is not None:
            return str(value)
    raise ValueError(f"missing required field {keys[0]}")


def _optional_text(obj: Any, *keys: str) -> str | None:
    try:
        return _text(obj, *keys)
    except ValueError:
        return None


def _public_event_value(event_type: str, payload: Any, token_id: str | None) -> dict[str, Any]:
    """Canonicalize documented public events without float conversion."""
    fields: dict[str, tuple[str, ...]] = {
        "last_trade_price": ("price", "size", "side", "fee_rate_bps", "transaction_hash"),
        "tick_size_change": ("old_tick_size", "old_tick", "tick_size", "new_tick_size"),
        "best_bid_ask": ("best_bid", "best_ask", "spread"),
    }
    value: dict[str, Any] = {"event_type": event_type}
    if token_id is not None:
        value["token_id"] = token_id
    for field in fields[event_type]:
        try:
            raw = _value(payload, field)
        except (KeyError, AttributeError):
            continue
        if raw is not None:
            value[field] = str(raw) if field not in {"side", "transaction_hash"} else str(raw)
    return value


def _items(obj: Any, key: str) -> Sequence[Any]:
    return _value(obj, key)


def _event_type(event: Any) -> str:
    return _text(event, "type", "event_type")


def _payload(event: Any) -> Any:
    return _value(event, "payload") if hasattr(event, "payload") or isinstance(event, Mapping) and "payload" in event else event


def _timestamp(obj: Any) -> datetime | None:
    try:
        value = _value(obj, "timestamp")
    except (KeyError, AttributeError):
        return None
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    return datetime.fromtimestamp(float(value) / (1000 if float(value) > 100_000_000_000 else 1), tz=UTC)


def _levels(payload: Any, key: str, *, reverse: bool) -> tuple[BookLevel, ...]:
    levels = [BookLevel(Decimal(str(_value(level, "price"))), Decimal(str(_value(level, "size")))) for level in _items(payload, key)]
    return tuple(sorted(levels, key=lambda level: level.price, reverse=reverse))
