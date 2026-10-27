"""Price chart endpoint: BTC/USDT history from our own 5-minute samples."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketPrice
from app.db.session import get_session
from app.market.collector import SYMBOL

router = APIRouter(prefix="/api")

TEHRAN = ZoneInfo("Asia/Tehran")
ORIGIN = datetime(2000, 1, 1, tzinfo=UTC)
Period = Literal["24h", "7d", "season"]
# One chart point per bucket keeps every range near 150-300 points.
BUCKET = {
    "24h": timedelta(minutes=5),
    "7d": timedelta(hours=1),
    "season": timedelta(hours=4),
}
SPAN = {"24h": timedelta(hours=24), "7d": timedelta(days=7)}


def window_start(period: Period, now: datetime) -> datetime:
    """Start of the range; a season starts at midnight on the 1st of the month in Tehran."""
    if period == "season":
        return now.astimezone(TEHRAN).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    return now - SPAN[period]


@router.get("/market/btc")
async def btc_chart(
    session: Annotated[AsyncSession, Depends(get_session)],
    period: Annotated[Period, Query(alias="range")] = "24h",
) -> dict:
    """Average price per bucket, oldest first."""
    bucket = func.date_bin(BUCKET[period], MarketPrice.ts, ORIGIN).label("bucket")
    rows = await session.execute(
        select(bucket, func.avg(MarketPrice.price))
        .where(MarketPrice.symbol == SYMBOL)
        .where(MarketPrice.ts >= window_start(period, datetime.now(UTC)))
        .group_by(bucket)
        .order_by(bucket)
    )
    points = [{"ts": ts, "price": round(float(price), 2)} for ts, price in rows]
    return {"symbol": SYMBOL, "range": period, "points": points}
