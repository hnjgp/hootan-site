"""Trading floor endpoints: start today's meeting (the worker holds it), watch it
live or replay the last one, and list past meetings.

Secret messages and the decision of the current trading day never leave the
server until the visitor's player cookie has today's prediction (CLAUDE.md 4.2).
"""

from datetime import UTC, date, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Player, Prediction, SessionEvent, TradingSession
from app.db.session import get_session
from app.game.players import current_player
from app.security.rate_limit import RateLimiter, limit_by_ip
from app.trading.run import get_or_create, trading_day

router = APIRouter(prefix="/api/trading")

START_LIMITERS = (RateLimiter(5, timedelta(days=1)),)
start_limits = limit_by_ip(*START_LIMITERS)
# Today's own meeting is shown in these states; otherwise the last done one.
SHOWN_TODAY = ("scheduled", "running", "done")


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


def event_out(event: SessionEvent, hide: bool) -> dict:
    """An event for the page; a hidden one keeps only who spoke and when."""
    out = {"seq": event.seq, "agent": event.agent, "kind": event.kind}
    if hide:
        return out | {"hidden": True}
    return out | {
        "hidden": False,
        "text_en": event.text_en,
        "text_fa": event.text_fa,
        "payload": event.payload,
    }


async def has_predicted(
    session: AsyncSession, player: Player | None, today: date
) -> bool:
    """True when the player already predicted this trading day."""
    if player is None:
        return False
    found = await session.scalar(
        select(Prediction.id)
        .where(Prediction.player_id == player.id)
        .where(Prediction.game_date == today)
    )
    return found is not None


def session_out(row: TradingSession, today: date, unlocked: bool) -> dict:
    """Summary of a meeting; today's decision stays secret until the visitor predicts."""
    secret = row.session_date == today and not unlocked
    return {
        "id": row.id,
        "session_date": row.session_date,
        "status": row.status,
        "price": row.price,
        "decision": None if secret else row.decision,
        "qty": None if secret else row.qty,
        "started_at": row.started_at,
        "finished_at": row.finished_at,
    }


@router.get("/sessions/today")
async def today_session(
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player | None, Depends(current_player)],
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
        shown = await session.scalar(
            select(TradingSession)
            .where(TradingSession.status == "done")
            .where(TradingSession.session_date < today)
            .order_by(TradingSession.session_date.desc())
            .limit(1)
        )
    body = {"trading_day": today, "today_status": own.status if own else None}
    if shown is None:
        return body | {"session": None}
    events = await session.scalars(
        select(SessionEvent)
        .where(SessionEvent.session_id == shown.id)
        .where(SessionEvent.seq > after)
        .order_by(SessionEvent.seq)
    )
    unlocked = await has_predicted(session, player, today)
    secret = shown.session_date == today and not unlocked
    return body | {
        "session": session_out(shown, today, unlocked)
        | {"events": [event_out(e, secret and e.is_secret) for e in events]}
    }


@router.get("/sessions/history")
async def history(
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player | None, Depends(current_player)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> list[dict]:
    """Past and current meetings, newest first, without their events."""
    today = trading_day(datetime.now(UTC))
    rows = await session.scalars(
        select(TradingSession).order_by(TradingSession.session_date.desc()).limit(limit)
    )
    unlocked = await has_predicted(session, player, today)
    return [session_out(r, today, unlocked) for r in rows]
