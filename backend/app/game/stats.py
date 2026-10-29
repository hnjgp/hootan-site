"""Numbers beside the game: how often the AI team called the day right this season,
how many players are ahead of it, and its trades for the chart markers. No LLM."""

from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketPrice, PortfolioTrade, TradingSession
from app.game.scoring import AI_DIRECTION, settle
from app.game.season import season_day
from app.llm.budget import TEHRAN

TRADES = 60


async def team_accuracy(db: AsyncSession, now: datetime) -> tuple[int, int]:
    """(right, decided) for this season's BUY/SELL meetings, judged like a prediction.

    A meeting is judged at the first price from 09:00 Tehran the next day; a draw or
    a day not over yet is not counted.
    """
    rows = await db.execute(
        select(
            TradingSession.session_date, TradingSession.decision, TradingSession.price
        )
        .where(TradingSession.status == "done")
        .where(TradingSession.decision.in_(AI_DIRECTION))
        .where(TradingSession.session_date >= season_day(now))
    )
    right = decided = 0
    for day, decision, price in rows:
        end = datetime.combine(day + timedelta(days=1), time(9), TEHRAN)
        close = await db.scalar(
            select(MarketPrice.price)
            .where(MarketPrice.ts >= end)
            .order_by(MarketPrice.ts)
            .limit(1)
        )
        if close is None or price is None:
            continue
        result = settle(AI_DIRECTION[decision], 1, price, close, None).result
        if result != "draw":
            decided += 1
            right += result == "win"
    return right, decided


def players_ahead(rows: list[dict]) -> tuple[int, int]:
    """(ahead, players) on a leaderboard: players with a better return than the AI row."""
    ai = next(r["return_pct"] for r in rows if r["is_ai"])
    players = [r for r in rows if not r["is_ai"]]
    return sum(r["return_pct"] > ai for r in players), len(players)


async def recent_trades(db: AsyncSession) -> list[dict]:
    """The team's latest trades, oldest first."""
    rows = await db.scalars(
        select(PortfolioTrade).order_by(PortfolioTrade.created_at.desc()).limit(TRADES)
    )
    return [
        {"ts": t.created_at, "side": t.side, "price": t.price}
        for t in reversed(list(rows))
    ]
