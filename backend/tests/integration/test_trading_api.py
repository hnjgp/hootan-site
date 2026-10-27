from datetime import UTC, datetime

import httpx2
import pytest
from sqlalchemy import func, select

from app.db.models import TradingSession
from app.db.session import get_session
from app.main import app
from app.trading.api import START_LIMITERS
from app.trading.run import trading_day

START = "/api/trading/sessions/today/start"


@pytest.fixture
async def api(session):
    """HTTP client on the app using the test session; rate limits start empty."""
    for limiter in START_LIMITERS:
        limiter.hits.clear()
    app.dependency_overrides[get_session] = lambda: session
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


async def test_first_click_queues_todays_meeting(api, session):
    response = await api.post(START)

    assert response.status_code == 200
    body = response.json()
    assert body["first"] is True
    assert body["status"] == "scheduled"
    assert body["session_date"] == str(trading_day(datetime.now(UTC)))


async def test_second_click_joins_the_same_meeting(api, session):
    first = (await api.post(START)).json()
    second = (await api.post(START)).json()

    assert second["first"] is False
    assert second["session_id"] == first["session_id"]
    count = await session.scalar(select(func.count()).select_from(TradingSession))
    assert count == 1


async def test_sixth_click_in_a_day_is_limited(api):
    for _ in range(5):
        assert (await api.post(START)).status_code == 200

    assert (await api.post(START)).status_code == 429
