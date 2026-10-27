"""The data analyst's numbers, computed in Python at the moment of the meeting."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketPrice
from app.market.collector import SYMBOL
from app.market.indicators import daily_indicators
from app.market.prices import fetch_btc_price, fetch_daily_closes, make_client


async def range_24h(db: AsyncSession) -> tuple[float | None, float | None]:
    """Lowest and highest stored 5-minute price of the last 24 hours."""
    low, high = (
        await db.execute(
            select(func.min(MarketPrice.price), func.max(MarketPrice.price))
            .where(MarketPrice.symbol == SYMBOL)
            .where(MarketPrice.ts >= datetime.now(UTC) - timedelta(hours=24))
        )
    ).one()
    return (float(low) if low else None, float(high) if high else None)


async def market_snapshot(db: AsyncSession) -> dict:
    """Live price, daily RSI and averages, and the 24h range, as plain floats.

    Raises PriceUnavailable when every price source fails.
    """
    async with make_client() as client:
        quote = await fetch_btc_price(client)
        closes = await fetch_daily_closes(client)
    indicators = daily_indicators(closes)
    low, high = await range_24h(db)
    return {
        "price": float(quote.price),
        "low_24h": low,
        "high_24h": high,
        "rsi_14": indicators["rsi_14"],
        "sma_7": indicators["sma_7"],
        "sma_30": indicators["sma_30"],
    }
