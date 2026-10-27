"""At 09:00 Tehran the previous trading day's predictions are settled (no LLM)."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Player, Prediction, TradingSession
from app.game.scoring import AI_DIRECTION, settle
from app.trading.run import trading_day


async def settle_predictions(db: AsyncSession, price: Decimal, now: datetime) -> int:
    """Settle every open prediction of an earlier trading day at `price`; return how many.

    The AI direction is the decision of that day's finished meeting; without one, no bonus.
    """
    rows = list(
        await db.scalars(
            select(Prediction)
            .where(Prediction.result.is_(None))
            .where(Prediction.game_date < trading_day(now))
        )
    )
    decisions = dict(
        (
            await db.execute(
                select(TradingSession.session_date, TradingSession.decision)
                .where(TradingSession.status == "done")
                .where(TradingSession.session_date.in_({p.game_date for p in rows}))
            )
        ).all()
    )
    for p in rows:
        ai = AI_DIRECTION.get(decisions.get(p.game_date))
        out = settle(p.direction, p.stake_usd, p.ref_price, price, ai)
        p.result, p.pnl_usd = out.result, out.pnl_usd
        await db.execute(
            update(Player)
            .where(Player.id == p.player_id)
            .values(balance_usd=Player.balance_usd + out.pnl_usd)
        )
    await db.commit()
    return len(rows)
