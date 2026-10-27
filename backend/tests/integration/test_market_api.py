from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx2
import pytest

from app.db.models import MarketPrice
from app.db.session import get_session
from app.main import app
from app.market.api import window_start

# Three hours ago, on the hour: two samples share one hourly bucket.
BASE = datetime.now(UTC).replace(minute=0, second=0, microsecond=0) - timedelta(hours=3)


@pytest.fixture
async def api(session):
    """HTTP client on the app with three stored prices."""
    for ts, price in [
        (BASE - timedelta(days=2), "70000"),
        (BASE, "80000"),
        (BASE + timedelta(minutes=5), "81000"),
    ]:
        session.add(
            MarketPrice(ts=ts, symbol="BTCUSDT", price=Decimal(price), source="nobitex")
        )
    await session.commit()

    app.dependency_overrides[get_session] = lambda: session
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def prices(api, period: str) -> list[float]:
    response = await api.get("/api/market/btc", params={"range": period})
    assert response.status_code == 200
    return [p["price"] for p in response.json()["points"]]


async def test_24h_keeps_only_the_last_day_at_five_minutes(api):
    assert await prices(api, "24h") == [80000.0, 81000.0]


async def test_7d_averages_each_hour(api):
    assert await prices(api, "7d") == [70000.0, 80500.0]


async def test_unknown_range_is_rejected(api):
    response = await api.get("/api/market/btc", params={"range": "1y"})
    assert response.status_code == 422


def test_season_starts_on_the_first_at_tehran_midnight():
    now = datetime(2026, 10, 27, 8, 0, tzinfo=UTC)
    assert window_start("season", now) == datetime(2026, 9, 30, 20, 30, tzinfo=UTC)
