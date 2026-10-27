from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select

from app.db.models import PortfolioSnapshot, PortfolioTrade, TradingSession
from app.trading.guard import check_stop, take_snapshot
from app.trading.portfolio import load_portfolio

TS = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)


async def bought(session) -> None:
    """A first meeting at 80,000 that bought 0.25 BTC with a stop at 76,000."""
    row = TradingSession(
        session_date=date(2026, 10, 27), status="done", price=Decimal(80_000)
    )
    session.add(row)
    await session.flush()
    session.add(
        PortfolioTrade(
            session_id=row.id,
            side="BUY",
            qty=Decimal("0.25"),
            price=Decimal(80_000),
            stop_price=Decimal(76_000),
            reason="test",
        )
    )
    await session.commit()


async def test_price_above_the_stop_keeps_the_position(session):
    await bought(session)

    assert await check_stop(session, Decimal(76_001)) is None
    assert (await load_portfolio(session)).btc_qty == Decimal("0.25")


async def test_price_at_or_below_the_stop_sells_everything_at_that_price(session):
    await bought(session)

    sale = await check_stop(session, Decimal(75_000))

    assert (sale.side, sale.qty, sale.price, sale.session_id) == (
        "SELL",
        Decimal("0.25"),
        Decimal(75_000),
        None,
    )
    portfolio = await load_portfolio(session)
    assert (portfolio.btc_qty, portfolio.stop_price) == (0, None)
    assert await check_stop(session, Decimal(70_000)) is None


async def test_snapshot_compares_with_buy_and_hold_once_per_time(session):
    await bought(session)

    await take_snapshot(session, Decimal(88_000), TS)
    await take_snapshot(session, Decimal(90_000), TS)

    snapshots = list(await session.scalars(select(PortfolioSnapshot)))
    assert len(snapshots) == 1
    snap = snapshots[0]
    assert snap.value_usd == Decimal(80_000) + Decimal("0.25") * 88_000
    assert snap.hold_value_usd == Decimal(110_000)


async def test_snapshot_before_any_meeting_is_all_cash(session):
    await take_snapshot(session, Decimal(88_000), TS)

    snap = await session.scalar(select(PortfolioSnapshot))
    assert snap.value_usd == snap.hold_value_usd == Decimal(100_000)
    count = await session.scalar(select(func.count()).select_from(PortfolioTrade))
    assert count == 0
