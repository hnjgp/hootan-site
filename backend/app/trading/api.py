"""Trading floor endpoints: start today's meeting; the worker holds it."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.security.rate_limit import RateLimiter, limit_by_ip
from app.trading.run import get_or_create, trading_day

router = APIRouter(prefix="/api/trading")

START_LIMITERS = (RateLimiter(5, timedelta(days=1)),)
start_limits = limit_by_ip(*START_LIMITERS)


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
