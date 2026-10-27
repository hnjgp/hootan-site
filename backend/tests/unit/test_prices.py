from decimal import Decimal

import httpx2
import pytest

from app.market.prices import PriceUnavailable, Quote, fetch_btc_price

NOBITEX_OK = {"status": "ok", "stats": {"btc-usdt": {"latest": "80525"}}}
WALLEX_OK = {"result": {"latestTrades": [{"price": "80325.0000000000000000"}]}}


def client_for(handler) -> httpx2.AsyncClient:
    """Client whose requests go to a fake exchange instead of the network."""
    return httpx2.AsyncClient(transport=httpx2.MockTransport(handler))


async def test_uses_nobitex_when_it_works():
    async with client_for(lambda req: httpx2.Response(200, json=NOBITEX_OK)) as c:
        quote = await fetch_btc_price(c, backoff=0)
    assert quote.price == Decimal("80525")
    assert quote.source == "nobitex"


async def test_falls_back_to_wallex_after_nobitex_retries():
    calls = []

    def handler(req):
        calls.append(req.url.host)
        if req.url.host == "apiv2.nobitex.ir":
            return httpx2.Response(503)
        return httpx2.Response(200, json=WALLEX_OK)

    async with client_for(handler) as c:
        quote = await fetch_btc_price(c, backoff=0)
    assert quote == Quote(Decimal("80325"), "wallex")
    assert calls.count("apiv2.nobitex.ir") == 3


async def test_bad_reply_counts_as_failure():
    async with client_for(lambda req: httpx2.Response(200, json={"status": "failed"})) as c:
        with pytest.raises(PriceUnavailable):
            await fetch_btc_price(c, backoff=0)
