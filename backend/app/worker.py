"""Scheduled jobs: the BTC price every 5 minutes (no LLM), and queued trading
meetings every 5 seconds (a visitor's click queues at most one per day)."""

import asyncio
import logging
from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.db.session import SessionLocal
from app.llm.client import LLMClient
from app.market.collector import collect_price
from app.market.prices import PriceUnavailable
from app.trading.run import claim_scheduled, fail_stale, hold_meeting

log = logging.getLogger("worker")


async def price_job() -> None:
    """Fetch and store one price; if every source fails, log it and wait for the next run."""
    try:
        async with SessionLocal() as session:
            quote = await collect_price(session)
        log.info("price %s from %s", quote.price, quote.source)
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
    logging.getLogger("httpx").setLevel(logging.WARNING)
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
