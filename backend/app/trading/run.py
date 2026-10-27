"""Run one trading day's meeting from start to finish.

Manual run from backend/: uv run python -m app.trading.run [--date YYYY-MM-DD]
"""

import argparse
import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import LLMUsage, TradingSession
from app.db.session import SessionLocal
from app.llm.budget import TEHRAN, BudgetExceeded, check_budget
from app.llm.client import LLMClient
from app.trading.graph import run_meeting
from app.trading.market import market_snapshot
from app.trading.portfolio import load_portfolio
from app.trading.translate import translate_session

log = logging.getLogger("trading")
DAY_START = timedelta(hours=9)
# A real meeting takes about a minute; one still running after this was abandoned.
STALE_AFTER = timedelta(minutes=10)


def trading_day(now: datetime) -> date:
    """A trading day starts at 09:00 Tehran; before that it is still yesterday's."""
    return (now.astimezone(TEHRAN) - DAY_START).date()


async def get_or_create(
    db: AsyncSession, day: date, status: str
) -> tuple[TradingSession, bool]:
    """The day's session row and whether this call created it (one row per day)."""
    created = await db.scalar(
        insert(TradingSession)
        .values(session_date=day, status=status)
        .on_conflict_do_nothing()
        .returning(TradingSession.id)
    )
    await db.commit()
    row = await db.scalar(
        select(TradingSession).where(TradingSession.session_date == day)
    )
    return row, created is not None


async def claim_scheduled(db: AsyncSession) -> list[TradingSession]:
    """Move queued sessions to running in one statement and return them.

    Postgres locks each row it updates, so two workers never claim the same one.
    """
    ids = await db.scalars(
        update(TradingSession)
        .where(TradingSession.status == "scheduled")
        .values(status="running", started_at=func.now())
        .returning(TradingSession.id)
    )
    ids = list(ids)
    await db.commit()
    if not ids:
        return []
    return list(
        await db.scalars(select(TradingSession).where(TradingSession.id.in_(ids)))
    )


async def fail_stale(db: AsyncSession, now: datetime) -> int:
    """Mark sessions left running by a stopped worker as failed; return how many."""
    result = await db.execute(
        update(TradingSession)
        .where(TradingSession.status == "running")
        .where(TradingSession.started_at < now - STALE_AFTER)
        .values(status="failed", finished_at=now)
    )
    await db.commit()
    return result.rowcount


async def hold_meeting(
    db: AsyncSession,
    llm: LLMClient,
    row: TradingSession,
    load_market: Callable[[AsyncSession], Awaitable[dict]] = market_snapshot,
) -> TradingSession:
    """Meeting, trade and translation for `row`; ends as done, skipped or failed.

    Skipped means the trading budget was used up; the previous meeting is replayed.
    """
    started, day = datetime.now(UTC), row.session_date
    row.status, row.started_at = "running", started
    await db.commit()
    try:
        await check_budget(db, "trading", llm.settings)
        market = await load_market(db)
        portfolio = await load_portfolio(db)
        await run_meeting(db, llm, row, market, portfolio)
        await translate_session(db, llm, row.id)
        row.status = "done"
    except BudgetExceeded:
        await db.rollback()
        row.status = "skipped"
    except Exception:
        log.exception("trading session %s failed", day)
        await db.rollback()
        row.status = "failed"
    row.finished_at = datetime.now(UTC)
    row.cost_usd = await db.scalar(
        select(func.coalesce(func.sum(LLMUsage.cost_usd), 0))
        .where(LLMUsage.feature == "trading")
        .where(LLMUsage.ts >= started)
    )
    await db.commit()
    await db.refresh(row)  # a rollback expired the row; reload it for the caller
    return row


async def _main() -> None:
    parser = argparse.ArgumentParser(description="Run one trading meeting.")
    parser.add_argument("--date", type=date.fromisoformat)
    args = parser.parse_args()
    day = args.date or trading_day(datetime.now(UTC))
    logging.basicConfig(level=logging.INFO)
    async with SessionLocal() as db:
        row, created = await get_or_create(db, day, "scheduled")
        if not created and row.status != "scheduled":
            print(f"{day}: a session already exists ({row.status}); nothing to do.")
            return
        row = await hold_meeting(db, LLMClient(get_settings()), row)
    print(
        f"{day}: {row.status}, {row.decision} {row.qty} at {row.price}, cost {row.cost_usd}"
    )


if __name__ == "__main__":
    asyncio.run(_main())
