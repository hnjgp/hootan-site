"""ORM models for the core tables (CLAUDE.md section 7). Times are timestamptz in UTC."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def created_at_column() -> Mapped[datetime]:
    """Timestamp set by the database at insert time."""
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Player(Base):
    """Anonymous player identified by a cookie UUID and a nickname."""

    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nickname: Mapped[str] = mapped_column(String(20), unique=True)
    recovery_token_hash: Mapped[str | None] = mapped_column(String(64))
    created_ip_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = created_at_column()


class Prediction(Base):
    """One up/down prediction per player per trading day."""

    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("player_id", "game_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE")
    )
    game_date: Mapped[date] = mapped_column(Date)
    direction: Mapped[str] = mapped_column(String(4))
    stake: Mapped[int] = mapped_column(Integer)
    ref_price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    result: Mapped[str | None] = mapped_column(String(4))
    points: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = created_at_column()


class MarketPrice(Base):
    """Price sample every 5 minutes; one row per symbol and timestamp."""

    __tablename__ = "market_prices"
    __table_args__ = (UniqueConstraint("symbol", "ts"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    symbol: Mapped[str] = mapped_column(String(16))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    source: Mapped[str] = mapped_column(String(32))


class TradingSession(Base):
    """The AI team's meeting; at most one per trading day."""

    __tablename__ = "trading_sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_date: Mapped[date] = mapped_column(Date, unique=True)
    status: Mapped[str] = mapped_column(String(16))
    decision: Mapped[str | None] = mapped_column(String(4))
    qty: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6), default=Decimal(0))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SessionEvent(Base):
    """One recorded step of a trading session, used for live view and replay."""

    __tablename__ = "session_events"
    __table_args__ = (UniqueConstraint("session_id", "seq"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("trading_sessions.id", ondelete="CASCADE")
    )
    seq: Mapped[int] = mapped_column(Integer)
    agent: Mapped[str] = mapped_column(String(32))
    kind: Mapped[str] = mapped_column(String(16))
    text_en: Mapped[str] = mapped_column(Text)
    text_fa: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict | None] = mapped_column(JSONB)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = created_at_column()


class LLMUsage(Base):
    """Cost record of a single LLM call; the budget guard sums these."""

    __tablename__ = "llm_usage"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    feature: Mapped[str] = mapped_column(String(16))
    model: Mapped[str] = mapped_column(String(64))
    tokens_in: Mapped[int] = mapped_column(Integer)
    tokens_out: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6))
