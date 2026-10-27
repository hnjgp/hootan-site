"""Scheduled jobs (no LLM): fetch the BTC price every 5 minutes."""

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db.session import SessionLocal
from app.market.collector import collect_price
from app.market.prices import PriceUnavailable

log = logging.getLogger("worker")


async def price_job() -> None:
    """Fetch and store one price; if every source fails, log it and wait for the next run."""
    try:
        async with SessionLocal() as session:
            quote = await collect_price(session)
        log.info("price %s from %s", quote.price, quote.source)
    except PriceUnavailable:
        log.warning("price unavailable from every source")


async def main() -> None:
    """Run one price job right away, then on every 5-minute mark until stopped."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    scheduler = AsyncIOScheduler(timezone="Asia/Tehran")
    scheduler.add_job(price_job, "cron", minute="*/5")
    scheduler.start()
    await price_job()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
