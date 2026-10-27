"""Scheduled jobs: the BTC price, stop loss, settling the game after 09:00 and the
hourly snapshot every 5 minutes (no LLM), and queued trading meetings every 5
seconds (a visitor's click queues at most one per day)."""

import asyncio
import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.db.session import SessionLocal
from app.game.settle import settle_predictions
from app.llm.client import LLMClient
from app.market.collector import collect_price, slot_start
from app.market.prices import PriceUnavailable
from app.trading.guard import check_stop, take_snapshot
from app.trading.run import claim_scheduled, fail_stale, hold_meeting

log = logging.getLogger("worker")


async def price_job() -> None:
    """Store one price, check the stop loss, settle yesterday's predictions and, on
    the hour, snapshot the portfolio.

    At 09:00 the first run settles the day before; if every source fails, log it and
    the next run settles with its price.
    """
    try:
        async with SessionLocal() as session:
            quote = await collect_price(session)
            log.info("price %s from %s", quote.price, quote.source)
            if sale := await check_stop(session, quote.price):
                log.warning("stop loss: sold %s BTC at %s", sale.qty, sale.price)
            if settled := await settle_predictions(
                session, quote.price, datetime.now(UTC)
            ):
                log.info("settled %s predictions at %s", settled, quote.price)
            slot = slot_start(datetime.now(UTC))
            if slot.minute == 0:
                await take_snapshot(session, quote.price, slot)
    except PriceUnavailable:
        log.warning("price unavailable from every source")


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
    scheduler.start()
    await price_job()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
