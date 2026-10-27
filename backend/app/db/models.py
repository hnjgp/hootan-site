"""ORM models for the core tables (CLAUDE.md section 7). Times are timestamptz in UTC."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
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

# Size of text-embedding-3-small vectors; changing the model needs a new migration.
EMBED_DIM = 1536


def created_at_column() -> Mapped[datetime]:
    """Timestamp set by the database at insert time."""
    return mapped_column(DateTime(timezone=True), server_default=func.now())


class Player(Base):
    """Anonymous player identified by a signed cookie and a nickname; virtual USD wallet."""

    __tablename__ = "players"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nickname: Mapped[str] = mapped_column(String(20), unique=True)
    balance_usd: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal(100_000), server_default="100000"
    )
    recovery_token_hash: Mapped[str | None] = mapped_column(String(64))
    created_ip_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = created_at_column()


class Prediction(Base):
    """One up/down prediction per player per trading day, staking a share of the wallet."""

    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("player_id", "game_date"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE")
    )
    game_date: Mapped[date] = mapped_column(Date)
    direction: Mapped[str] = mapped_column(String(4))
    stake_pct: Mapped[int] = mapped_column(Integer)
    stake_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    ref_price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    result: Mapped[str | None] = mapped_column(String(4))
    pnl_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
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


class PortfolioTrade(Base):
    """One buy or sell of the AI team; the portfolio is the sum of these.

    session_id is empty for a stop-loss sell made by code between sessions.
    """

    __tablename__ = "portfolio_trades"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("trading_sessions.id", ondelete="CASCADE")
    )
    side: Mapped[str] = mapped_column(String(4))
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    stop_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()


class PortfolioSnapshot(Base):
    """Portfolio value at one moment next to the buy-and-hold value, for the chart."""

    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), unique=True)
    cash: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    btc_qty: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    value_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    hold_value_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2))


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


class Document(Base):
    """One knowledge file of the digital twin; `source` is its path inside knowledge/."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(200), unique=True)
    lang: Mapped[str] = mapped_column(String(8))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class DocChunk(Base):
    """A piece of a document with its embedding, searched by cosine distance."""

    __tablename__ = "doc_chunks"
    __table_args__ = (
        Index(
            "ix_doc_chunks_embedding",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM))
    meta: Mapped[dict | None] = mapped_column(JSONB)


class ChatLog(Base):
    """One twin question and its answer; token fields are empty when no LLM was called."""

    __tablename__ = "chat_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    visitor_id: Mapped[str] = mapped_column(String(64), index=True)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    sources: Mapped[list | None] = mapped_column(JSONB)
    model: Mapped[str | None] = mapped_column(String(64))
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 6))
    created_at: Mapped[datetime] = created_at_column()


class JobFitRequest(Base):
    """One job ad a visitor pasted and the structured fit result for it."""

    __tablename__ = "jobfit_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    visitor_id: Mapped[str] = mapped_column(String(64), index=True)
    jd_text: Mapped[str] = mapped_column(Text)
    lang: Mapped[str] = mapped_column(String(8))
    score: Mapped[int] = mapped_column(Integer)
    result: Mapped[dict] = mapped_column(JSONB)
    model: Mapped[str] = mapped_column(String(64))
    tokens_in: Mapped[int] = mapped_column(Integer)
    tokens_out: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 6))
    created_at: Mapped[datetime] = created_at_column()


class Lead(Base):
    """Email a visitor left for Hootan, with the question that led to it."""

    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    context: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_column()
