"""ORM models for the core tables (CLAUDE.md section 7). Times are timestamptz in UTC."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
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
    """A registered player of the demo exchange; the signed cookie says who is logged in.

    Cash is not stored: it follows from the player's positions (app/exchange).

    The password is stored as typed: Hootan wants to read it in the admin panel
    (Decision Log 2026-10-30). Email is required and unique ignoring case, phone
    optional. A password reset code is kept only as a hash, for 15 minutes.
    """

    __tablename__ = "players"
    __table_args__ = (
        Index("uq_players_email", func.lower(Column("email")), unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nickname: Mapped[str] = mapped_column(String(20), unique=True)
    password: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(20))
    avatar: Mapped[bytes | None] = mapped_column(LargeBinary)
    # BTC price at sign-up: what 10,000 USD held since then would be worth.
    signup_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    reset_code_hash: Mapped[str | None] = mapped_column(String(64))
    reset_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_ip_hash: Mapped[str | None] = mapped_column(String(64))
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
    # LONG or SHORT (opened a position), CLOSE (only closed) or HOLD.
    decision: Mapped[str | None] = mapped_column(String(8))
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
    created_at: Mapped[datetime] = created_at_column()


class Position(Base):
    """A long or short BTC position with isolated margin; player_id is empty for the AI team.

    fee_usd is every fee paid so far (opening, then closing). pnl_usd, set at closing,
    is the position's net effect on cash: what came back minus margin and fees.
    """

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("trading_sessions.id", ondelete="SET NULL")
    )
    side: Mapped[str] = mapped_column(String(5))
    entry_price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    margin_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    leverage: Mapped[int] = mapped_column(Integer)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    tp_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    sl_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    liq_price: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    fee_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    opened_at: Mapped[datetime] = created_at_column()
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    close_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    close_reason: Mapped[str | None] = mapped_column(String(8))
    pnl_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))


class EquitySnapshot(Base):
    """A player's (or, with no player, the team's) equity on the first check of a
    trading day: the start of the month's return and of the team's buy-and-hold."""

    __tablename__ = "equity_snapshots"
    __table_args__ = (
        UniqueConstraint("day", "player_id", postgresql_nulls_not_distinct=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    day: Mapped[date] = mapped_column(Date)
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE")
    )
    equity_usd: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 2))


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
    tokens_cached: Mapped[int] = mapped_column(Integer, server_default="0")
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
    # The logged-in player who asked, if any (shown in the admin panel).
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL")
    )
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
    # The logged-in player who asked, if any (shown in the admin panel).
    player_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL")
    )
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
