"""Fetch the BTC price and store it in market_prices, one row per 5-minute slot."""

import asyncio
from datetime import UTC, datetime

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketPrice
from app.db.session import SessionLocal
from app.market.prices import Quote, fetch_btc_price, make_client

SYMBOL = "BTCUSDT"


def slot_start(ts: datetime) -> datetime:
    """Round a time down to its 5-minute slot, e.g. 10:07:42 -> 10:05:00."""
    return ts.replace(minute=ts.minute - ts.minute % 5, second=0, microsecond=0)


async def save_price(session: AsyncSession, quote: Quote, ts: datetime) -> bool:
    """Store the quote in ts's slot; return False if that slot already has a price."""
    stmt = (
        insert(MarketPrice)
        .values(
            ts=slot_start(ts), symbol=SYMBOL, price=quote.price, source=quote.source
        )
        .on_conflict_do_nothing()
        .returning(MarketPrice.id)
    )
    saved = (await session.execute(stmt)).scalar() is not None
    await session.commit()
    return saved


async def collect_price(session: AsyncSession) -> Quote:
    """Fetch the current price and save it for the current slot."""
    async with make_client() as client:
        quote = await fetch_btc_price(client)
    await save_price(session, quote, datetime.now(UTC))
    return quote


async def _main() -> None:
    async with SessionLocal() as session:
        print(await collect_price(session))


if __name__ == "__main__":
    asyncio.run(_main())
