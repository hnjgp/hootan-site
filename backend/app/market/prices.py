"""BTC/USDT price from Iranian exchanges: Nobitex first, Wallex as fallback."""

import asyncio
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

import httpx2
import pandas as pd

NOBITEX_URL = "https://apiv2.nobitex.ir/market/stats"
NOBITEX_HISTORY_URL = "https://apiv2.nobitex.ir/market/udf/history"
WALLEX_URL = "https://api.wallex.ir/v1/trades"
RETRIES = 2


class PriceUnavailable(Exception):
    """Every source failed after its retries."""


@dataclass
class Quote:
    """One price and the exchange it came from."""

    price: Decimal
    source: str


def make_client() -> httpx2.AsyncClient:
    """HTTP client with a 10 s timeout that ignores the system proxy, like the Iran server."""
    return httpx2.AsyncClient(timeout=10, trust_env=False)


async def fetch_nobitex(client: httpx2.AsyncClient) -> Decimal:
    """Latest trade price from Nobitex market stats."""
    r = await client.get(NOBITEX_URL, params={"srcCurrency": "btc", "dstCurrency": "usdt"})
    r.raise_for_status()
    return Decimal(r.json()["stats"]["btc-usdt"]["latest"])


async def fetch_wallex(client: httpx2.AsyncClient) -> Decimal:
    """Price of the newest trade on Wallex."""
    r = await client.get(WALLEX_URL, params={"symbol": "BTCUSDT"})
    r.raise_for_status()
    return Decimal(r.json()["result"]["latestTrades"][0]["price"])


SOURCES = [("nobitex", fetch_nobitex), ("wallex", fetch_wallex)]


async def fetch_btc_price(client: httpx2.AsyncClient, backoff: float = 1) -> Quote:
    """Try each source in order, retrying with backoff; raise PriceUnavailable if all fail."""
    for name, fetch in SOURCES:
        for attempt in range(RETRIES + 1):
            try:
                return Quote(await fetch(client), name)
            except (httpx2.HTTPError, KeyError, IndexError, InvalidOperation):
                if attempt < RETRIES:
                    await asyncio.sleep(backoff * 2**attempt)
    raise PriceUnavailable


async def fetch_daily_closes(client: httpx2.AsyncClient, days: int = 60) -> pd.Series:
    """Daily closes from Nobitex, oldest first; days start at Tehran midnight.

    The last value is today's unfinished candle, so its close is the current price.
    """
    now = int(time.time())
    params = {"symbol": "BTCUSDT", "resolution": "D", "from": now - days * 86400, "to": now}
    r = await client.get(NOBITEX_HISTORY_URL, params=params)
    r.raise_for_status()
    data = r.json()
    return pd.Series(data["c"], index=pd.to_datetime(data["t"], unit="s", utc=True))


async def _main() -> None:
    async with make_client() as client:
        print(await fetch_btc_price(client))


if __name__ == "__main__":
    asyncio.run(_main())
