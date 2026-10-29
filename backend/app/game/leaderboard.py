"""Leaderboard by percent return on equity: this Persian month, or all time from
10,000 USD. The AI team is one of the rows."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EquitySnapshot, Player
from app.exchange import book, calc
from app.game.season import season_day

Period = Literal["month", "all"]
AI_NAME = "AI Trading Team"


def pct(gain: Decimal, base: Decimal) -> float:
    """Gain as a percent of base, two decimals."""
    return round(float(gain / base * 100), 2)


async def month_starts(db: AsyncSession, now: datetime) -> dict:
    """Each owner's first equity snapshot of the season; without one, START_USD."""
    rows = await db.execute(
        select(EquitySnapshot.player_id, EquitySnapshot.equity_usd)
        .where(EquitySnapshot.day >= season_day(now))
        .order_by(EquitySnapshot.player_id, EquitySnapshot.day)
        .ext(distinct_on(EquitySnapshot.player_id))
    )
    return dict(rows.all())


async def leaderboard(
    db: AsyncSession, period: Period, price: Decimal, now: datetime
) -> list[dict]:
    """Every ranked row, best return first, each with its rank.

    Players appear after their first position; the team always appears.
    """
    found = await book.books(db)
    found.setdefault(None, book.Book())
    names = dict((await db.execute(select(Player.id, Player.nickname))).all())
    starts = await month_starts(db, now) if period == "month" else {}
    rows = []
    for owner, b in found.items():
        start = starts.get(owner, calc.START_USD)
        rows.append(
            {
                "nickname": AI_NAME if owner is None else names[owner],
                "return_pct": pct(b.equity(price) - start, start),
                "is_ai": owner is None,
            }
        )
    rows.sort(key=lambda r: r["return_pct"], reverse=True)
    return [{"rank": i} | r for i, r in enumerate(rows, start=1)]
