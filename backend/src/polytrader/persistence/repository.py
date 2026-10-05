import hashlib
import json
from decimal import Decimal
from typing import Any

from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from polytrader.evidence.models import EvidenceObservation


class Base(DeclarativeBase):
    pass


class FillRecord(Base):
    __tablename__ = "fills"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[str] = mapped_column(String(100), unique=True)
    token_id: Mapped[str] = mapped_column(String(200))
    side: Mapped[str] = mapped_column(String(4))
    quantity: Mapped[str] = mapped_column(String(40))
    price: Mapped[str] = mapped_column(String(40))
    fee: Mapped[str] = mapped_column(String(40))


class EvidenceRecord(Base):
    __tablename__ = "evidence"
    id: Mapped[int] = mapped_column(primary_key=True)
    provenance_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(100))
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_timestamp: Mapped[str] = mapped_column(String(50))
    collected_at: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(10000))
    revision: Mapped[str] = mapped_column(String(100))
    payload_hash: Mapped[str] = mapped_column(String(64))
    market_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    token_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    event_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    confidence: Mapped[str] = mapped_column(String(40))
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)


class PortfolioRepository:
    def __init__(self, database_url: str) -> None:
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)

    def record_fill(
        self, order_id: str, token_id: str, side: str, quantity: Decimal, price: Decimal, fee: Decimal
    ) -> None:
        with Session(self.engine) as session:
            session.add(FillRecord(
                order_id=order_id, token_id=token_id, side=side,
                quantity=str(quantity), price=str(price), fee=str(fee),
            ))
            session.commit()

    def fills(self) -> list[FillRecord]:
        with Session(self.engine) as session:
            return list(session.scalars(select(FillRecord).order_by(FillRecord.id)))

    @staticmethod
    def _provenance_key(observation: EvidenceObservation) -> str:
        material = "|".join((
            observation.source, observation.source_type,
            observation.source_timestamp.isoformat(), observation.revision,
            observation.payload_hash, observation.market_id or "",
            observation.token_id or "", observation.event_id or "",
        ))
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def record_evidence(self, observation: EvidenceObservation) -> EvidenceRecord:
        key = self._provenance_key(observation)
        encoded_value = json.dumps(observation.value, sort_keys=True, default=str)
        with Session(self.engine) as session:
            existing = session.scalar(select(EvidenceRecord).where(EvidenceRecord.provenance_key == key))
            if existing is not None:
                return existing
            record = EvidenceRecord(
                provenance_key=key, source=observation.source, source_type=observation.source_type,
                source_url=observation.source_url, source_timestamp=observation.source_timestamp.isoformat(),
                collected_at=observation.collected_at.isoformat(), value=encoded_value,
                revision=observation.revision, payload_hash=observation.payload_hash,
                market_id=observation.market_id, token_id=observation.token_id,
                event_id=observation.event_id, confidence=str(observation.confidence),
                model_version=observation.model_version,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def evidence(self) -> list[EvidenceRecord]:
        with Session(self.engine) as session:
            return list(session.scalars(select(EvidenceRecord).order_by(EvidenceRecord.id)))

    def state(self, starting_cash: Decimal) -> dict[str, Any]:
        """Rebuild a read-only portfolio view from auditable fills.

        The repository stores Decimal values as strings deliberately. This
        projection performs all arithmetic in Decimal and is safe to expose
        through the API without leaking ORM objects.
        """

        cash = starting_cash
        realized = Decimal("0")
        positions: dict[str, dict[str, Decimal]] = {}
        orders: list[dict[str, str]] = []
        for fill in self.fills():
            quantity, price, fee = Decimal(fill.quantity), Decimal(fill.price), Decimal(fill.fee)
            item = positions.setdefault(fill.token_id, {"quantity": Decimal("0"), "cost_basis": Decimal("0")})
            notional = quantity * price
            if fill.side == "BUY":
                cash -= notional + fee
                item["quantity"] += quantity
                item["cost_basis"] += notional + fee
            elif fill.side == "SELL":
                average_cost = item["cost_basis"] / item["quantity"] if item["quantity"] else Decimal("0")
                cash += notional - fee
                item["quantity"] -= quantity
                item["cost_basis"] -= average_cost * quantity
                realized += notional - fee - average_cost * quantity
            orders.append({
                "order_id": fill.order_id, "token_id": fill.token_id, "side": fill.side,
                "quantity": str(quantity), "price": str(price), "fee": str(fee),
            })
        positions = {key: value for key, value in positions.items() if value["quantity"] > 0}
        return {
            "cash": cash,
            "equity": cash + sum((item["cost_basis"] for item in positions.values()), Decimal("0")),
            "realized_pnl": realized,
            "positions": positions,
            "orders": orders,
        }

    def paper_performance(self, starting_cash: Decimal) -> dict[str, Decimal | int]:
        """Return an auditable paper scorecard derived from stored fills.

        Win rate counts closed SELL fills with positive realized P&L. With no
        closed exits, the rate is exactly zero; callers should display the
        zero-sample state rather than imply performance.
        """

        del starting_cash  # Reserved for future equity-series metrics.
        positions: dict[str, tuple[Decimal, Decimal]] = {}
        wins = losses = exits = 0
        fills = self.fills()
        for fill in fills:
            quantity, price, fee = Decimal(fill.quantity), Decimal(fill.price), Decimal(fill.fee)
            owned, cost_basis = positions.get(fill.token_id, (Decimal("0"), Decimal("0")))
            notional = quantity * price
            if fill.side == "BUY":
                positions[fill.token_id] = (owned + quantity, cost_basis + notional + fee)
                continue
            average_cost = cost_basis / owned if owned else Decimal("0")
            realized = notional - fee - average_cost * quantity
            exits += 1
            if realized > 0:
                wins += 1
            elif realized < 0:
                losses += 1
            positions[fill.token_id] = (owned - quantity, cost_basis - average_cost * quantity)
        win_rate = (Decimal(wins) / Decimal(exits) * Decimal("100")) if exits else Decimal("0")
        return {"fills": len(fills), "exits": exits, "wins": wins, "losses": losses, "win_rate": win_rate}
