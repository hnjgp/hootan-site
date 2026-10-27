"""Leaderboard by percent return: this Persian month, or all time from 100,000 USD."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketPrice, Player, PortfolioSnapshot, Prediction
from app.game.season import season_day, season_start
from app.trading.portfolio import INITIAL_CASH, load_portfolio

Period = Literal["month", "all"]
# A player appears after this many settled predictions.
MIN_PREDICTIONS = 3
AI_NAME = "AI Trading Team"
TOP = 50


def pct(gain: Decimal, base: Decimal) -> float:
    """Gain as a percent of base, two decimals."""
    return round(float(gain / base * 100), 2)


async def player_rows(db: AsyncSession, period: Period, now: datetime) -> list[dict]:
    """Players with enough settled predictions and their return for the period.

    A month's return is its P&L over the balance at the month's start (balance minus it).
    """
    in_season = Prediction.game_date >= season_day(now)
    month_pnl = func.coalesce(func.sum(Prediction.pnl_usd).filter(in_season), 0)
    query = (
        select(Player.nickname, Player.balance_usd, func.count(), month_pnl)
        .join(Prediction)
        .where(Prediction.result.is_not(None))
        .group_by(Player.id)
        .having(func.count() >= MIN_PREDICTIONS)
    )
    if period == "month":
        query = query.having(func.count().filter(in_season) > 0)
    rows = []
    for nickname, balance, count, pnl in await db.execute(query):
        if period == "month":
            ret = pct(pnl, balance - pnl)
        else:
            ret = pct(balance - INITIAL_CASH, INITIAL_CASH)
        rows.append(
            {
                "nickname": nickname,
                "return_pct": ret,
                "predictions": count,
                "is_ai": False,
            }
        )
    return rows


async def ai_row(db: AsyncSession, period: Period, now: datetime) -> dict:
    """The AI team's portfolio return at the latest price.

    The month starts from the first hourly snapshot of the season.
    """
    price = await db.scalar(
        select(MarketPrice.price).order_by(MarketPrice.ts.desc()).limit(1)
    )
    value = (await load_portfolio(db)).value(price)
    start = INITIAL_CASH
    if period == "month":
        first = await db.scalar(
            select(PortfolioSnapshot.value_usd)
            .where(PortfolioSnapshot.ts >= season_start(now))
            .order_by(PortfolioSnapshot.ts)
            .limit(1)
        )
        start = first or INITIAL_CASH
    return {
        "nickname": AI_NAME,
        "return_pct": pct(value - start, start),
        "predictions": None,
        "is_ai": True,
    }


async def leaderboard(db: AsyncSession, period: Period, now: datetime) -> list[dict]:
    """Top rows, best return first, the AI team among them, each with its rank."""
    rows = await player_rows(db, period, now) + [await ai_row(db, period, now)]
    rows.sort(key=lambda r: r["return_pct"], reverse=True)
    return [{"rank": i} | r for i, r in enumerate(rows[:TOP], start=1)]
