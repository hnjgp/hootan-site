"""Scheduled jobs, all without LLM except the meeting: the stored BTC price and the
daily equity snapshots every 5 minutes; take profit, stop loss and liquidation of
every position every 5 seconds; and queued trading meetings every 5 seconds (a
visitor's click queues at most one per day)."""

import asyncio
import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.db.session import SessionLocal
from app.exchange.book import check_triggers, take_snapshots
from app.llm.client import LLMClient
from app.market.collector import collect_price
from app.market.prices import PriceUnavailable, fetch_btc_price, make_client
from app.trading.run import claim_scheduled, fail_stale, hold_meeting, trading_day

log = logging.getLogger("worker")


async def price_job() -> None:
    """Store one price and, once per trading day, everyone's equity snapshot.

    The first run after 09:00 takes the day's snapshots; later runs find them taken.
    """
    try:
        async with SessionLocal() as session:
            quote = await collect_price(session)
            log.info("price %s from %s", quote.price, quote.source)
            await take_snapshots(session, quote.price, trading_day(datetime.now(UTC)))
    except PriceUnavailable:
        log.warning("price unavailable from every source")


async def position_job() -> None:
    """Close positions whose take profit, stop loss or liquidation the live price reached."""
    try:
        async with make_client() as client:
            price = (await fetch_btc_price(client, backoff=0.2)).price
    except PriceUnavailable:
        return
    async with SessionLocal() as session:
        for p in await check_triggers(session, price):
            log.info("position %s closed by %s at %s", p.id, p.close_reason, price)


async def session_job() -> None:
    """Hold every meeting a visitor queued; hold_meeting records its own failures."""
    async with SessionLocal() as session:
        for row in await claim_scheduled(session):
            log.info("trading session %s started", row.session_date)
            row = await hold_meeting(session, LLMClient(get_settings()), row)
            log.info("trading session %s %s", row.session_date, row.status)


async def main() -> None:
    """Fail meetings a stopped worker left running, then run the jobs until stopped."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    # Two lines per 5-second run would be about 35,000 lines a day.
    for name in ("httpx", "httpx2", "apscheduler.executors"):
        logging.getLogger(name).setLevel(logging.WARNING)
    async with SessionLocal() as session:
        if stale := await fail_stale(session, datetime.now(UTC)):
            log.warning("%s abandoned trading session(s) marked failed", stale)
    scheduler = AsyncIOScheduler(timezone="Asia/Tehran")
    scheduler.add_job(price_job, "cron", minute="*/5")
    scheduler.add_job(session_job, "interval", seconds=5, max_instances=1)
    scheduler.add_job(position_job, "interval", seconds=5, max_instances=1)
    scheduler.start()
    await price_job()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
