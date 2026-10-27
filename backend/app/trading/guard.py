"""Between meetings, in code only (no LLM): the stop loss and portfolio snapshots."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PortfolioSnapshot, PortfolioTrade, TradingSession
from app.trading.portfolio import INITIAL_CASH, hold_value, load_portfolio


async def check_stop(db: AsyncSession, price: Decimal) -> PortfolioTrade | None:
    """Sell all BTC at the current price if it fell to the stop; return the sale.

    The sale is at the price seen, which can be below the stop after a sharp drop.
    """
    portfolio = await load_portfolio(db)
    if not portfolio.stop_hit(price):
        return None
    trade = PortfolioTrade(
        side="SELL",
        qty=portfolio.btc_qty,
        price=price,
        reason=f"Stop loss at {portfolio.stop_price} hit at {price}",
    )
    db.add(trade)
    await db.commit()
    return trade


async def first_session_price(db: AsyncSession) -> Decimal | None:
    """BTC price at the first meeting, the start of the buy-and-hold comparison."""
    return await db.scalar(
        select(TradingSession.price)
        .where(TradingSession.price.is_not(None))
        .order_by(TradingSession.session_date)
        .limit(1)
    )


async def take_snapshot(db: AsyncSession, price: Decimal, ts: datetime) -> None:
    """Store the portfolio value and the buy-and-hold value at `ts` (once per ts)."""
    portfolio = await load_portfolio(db)
    first = await first_session_price(db)
    held = hold_value(first, price) if first else INITIAL_CASH
    await db.execute(
        insert(PortfolioSnapshot)
        .values(
            ts=ts,
            cash=portfolio.cash,
            btc_qty=portfolio.btc_qty,
            value_usd=portfolio.value(price),
            hold_value_usd=held,
        )
        .on_conflict_do_nothing()
    )
    await db.commit()
