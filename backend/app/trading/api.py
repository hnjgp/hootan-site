"""Trading floor endpoints: start today's meeting (the worker holds it), watch it
live or replay the last one, list past meetings, the team's running score and its
trades for the price chart.

Every visitor sees whole meetings, decisions included.
"""

from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketPrice, PortfolioTrade, SessionEvent, TradingSession
from app.db.session import get_session
from app.security.rate_limit import RateLimiter, limit_by_ip
from app.trading.guard import first_session_price
from app.trading.portfolio import INITIAL_CASH, hold_value, load_portfolio
from app.trading.run import get_or_create, trading_day

router = APIRouter(prefix="/api/trading")

START_LIMITERS = (RateLimiter(5, timedelta(days=1)),)
start_limits = limit_by_ip(*START_LIMITERS)
# Today's own meeting is shown in these states; otherwise the last done one.
SHOWN_TODAY = ("scheduled", "running", "done")
TRADES = 60


@router.post("/sessions/today/start", dependencies=[Depends(start_limits)])
async def start_today(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Queue today's meeting once; `first` tells the visitor they started it.

    The unique session_date makes two clicks at the same moment create one row.
    """
    day = trading_day(datetime.now(UTC))
    row, created = await get_or_create(session, day, "scheduled")
    return {
        "session_id": row.id,
        "session_date": row.session_date,
        "status": row.status,
        "first": created,
    }


def event_out(event: SessionEvent) -> dict:
    """One spoken turn of a meeting for the page."""
    return {
        "seq": event.seq,
        "agent": event.agent,
        "kind": event.kind,
        "text_en": event.text_en,
        "text_fa": event.text_fa,
        "payload": event.payload,
    }


def session_out(row: TradingSession) -> dict:
    """Summary of a meeting without its events."""
    return {
        "id": row.id,
        "session_date": row.session_date,
        "status": row.status,
        "price": row.price,
        "decision": row.decision,
        "qty": row.qty,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
    }


async def events_of(session: AsyncSession, row: TradingSession, after: int = 0) -> list:
    """The meeting's events after seq `after`, in speaking order."""
    rows = await session.scalars(
        select(SessionEvent)
        .where(SessionEvent.session_id == row.id)
        .where(SessionEvent.seq > after)
        .order_by(SessionEvent.seq)
    )
    return [event_out(e) for e in rows]


async def last_done(
    session: AsyncSession, before: date | None = None
) -> TradingSession | None:
    """The newest finished meeting, optionally before a day."""
    query = select(TradingSession).where(TradingSession.status == "done")
    if before is not None:
        query = query.where(TradingSession.session_date < before)
    return await session.scalar(
        query.order_by(TradingSession.session_date.desc()).limit(1)
    )


@router.get("/sessions/today")
async def today_session(
    session: Annotated[AsyncSession, Depends(get_session)],
    after: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    """The meeting to show, with its events after seq `after` (for live polling).

    `today_status` is empty until someone starts today's meeting; when it was
    skipped or failed, the last finished meeting is shown instead.
    """
    today = trading_day(datetime.now(UTC))
    own = await session.scalar(
        select(TradingSession).where(TradingSession.session_date == today)
    )
    shown = own
    if own is None or own.status not in SHOWN_TODAY:
        shown = await last_done(session, before=today)
    body = {"trading_day": today, "today_status": own.status if own else None}
    if shown is None:
        return body | {"session": None}
    return body | {
        "session": session_out(shown)
        | {"events": await events_of(session, shown, after)}
    }


@router.get("/sessions/history")
async def history(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[dict]:
    """Past and current meetings, newest first, without their events."""
    rows = await session.scalars(
        select(TradingSession).order_by(TradingSession.session_date.desc()).limit(limit)
    )
    return [session_out(r) for r in rows]


@router.get("/summary")
async def summary(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """The team's money against buy-and-hold at the latest price, and its last meeting."""
    today = trading_day(datetime.now(UTC))
    price = await session.scalar(
        select(MarketPrice.price).order_by(MarketPrice.ts.desc()).limit(1)
    )
    own = await session.scalar(
        select(TradingSession).where(TradingSession.session_date == today)
    )
    value = held = INITIAL_CASH
    if price is not None:
        value = (await load_portfolio(session)).value(price)
        first = await first_session_price(session)
        held = hold_value(first, price) if first else INITIAL_CASH
    last = await last_done(session)
    return {
        "trading_day": today,
        "today_status": own.status if own else None,
        "today_started_at": own.started_at if own else None,
        "start_usd": INITIAL_CASH,
        "value_usd": round(value, 2),
        "hold_usd": round(held, 2),
        "last": session_out(last) | {"events": await events_of(session, last)}
        if last
        else None,
    }


@router.get("/trades")
async def trades(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict]:
    """The team's latest buys and sells, oldest first, for the chart markers."""
    rows = await session.scalars(
        select(PortfolioTrade).order_by(PortfolioTrade.created_at.desc()).limit(TRADES)
    )
    return [
        {"ts": t.created_at, "side": t.side, "price": t.price}
        for t in reversed(list(rows))
    ]
