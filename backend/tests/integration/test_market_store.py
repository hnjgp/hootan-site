from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.db.models import MarketPrice
from app.market.collector import save_price
from app.market.prices import Quote


def at(minute: int, second: int) -> datetime:
    return datetime(2026, 10, 26, 10, minute, second, tzinfo=UTC)


async def test_one_row_per_five_minute_slot(session):
    first = await save_price(session, Quote(Decimal(80000), "nobitex"), at(7, 42))
    again = await save_price(session, Quote(Decimal(80100), "wallex"), at(9, 59))
    later = await save_price(session, Quote(Decimal(80200), "nobitex"), at(10, 0))

    assert (first, again, later) == (True, False, True)
    rows = (await session.scalars(select(MarketPrice).order_by(MarketPrice.ts))).all()
    assert [(r.ts, r.price, r.source) for r in rows] == [
        (at(5, 0), Decimal("80000.00"), "nobitex"),
        (at(10, 0), Decimal("80200.00"), "nobitex"),
    ]
