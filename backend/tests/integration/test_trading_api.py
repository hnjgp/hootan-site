from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx2
import pytest
from sqlalchemy import func, select

from app.db.models import MarketPrice, PortfolioTrade, SessionEvent, TradingSession
from app.db.session import get_session
from app.main import app
from app.trading.api import START_LIMITERS
from app.trading.run import trading_day

START = "/api/trading/sessions/today/start"
TODAY_URL = "/api/trading/sessions/today"
TODAY = trading_day(datetime.now(UTC))
YESTERDAY = TODAY - timedelta(days=1)
AGENTS = ["data", "news", "bull", "bear", "trader", "risk", "pm"]


async def meeting(session, day, status: str = "done") -> TradingSession:
    """A recorded BUY meeting with all seven speakers."""
    row = TradingSession(
        session_date=day,
        status=status,
        decision="BUY",
        qty=Decimal("0.25"),
        price=Decimal(80_000),
    )
    session.add(row)
    await session.flush()
    for seq, agent in enumerate(AGENTS, start=1):
        session.add(
            SessionEvent(
                session_id=row.id,
                seq=seq,
                agent=agent,
                kind="speech",
                text_en=f"{agent} speaks",
            )
        )
    await session.commit()
    return row


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


async def test_nothing_to_show_before_the_first_meeting(api):
    body = (await api.get(TODAY_URL)).json()

    assert body == {
        "trading_day": str(TODAY),
        "today_status": None,
        "session": None,
    }


async def test_todays_meeting_is_shown_in_full_to_everyone(api, session):
    await meeting(session, TODAY)

    shown = (await api.get(TODAY_URL)).json()["session"]

    assert shown["session_date"] == str(TODAY)
    assert shown["decision"] == "BUY"
    assert [e["agent"] for e in shown["events"]] == AGENTS
    assert shown["events"][6]["text_en"] == "pm speaks"


async def test_live_polling_returns_only_new_events(api, session):
    await meeting(session, TODAY, status="running")

    events = (await api.get(TODAY_URL, params={"after": 4})).json()["session"]["events"]

    assert [e["seq"] for e in events] == [5, 6, 7]


async def test_skipped_today_replays_yesterday_in_full(api, session):
    await meeting(session, YESTERDAY)
    session.add(TradingSession(session_date=TODAY, status="skipped"))
    await session.commit()

    body = (await api.get(TODAY_URL)).json()

    assert body["today_status"] == "skipped"
    shown = body["session"]
    assert shown["session_date"] == str(YESTERDAY)
    assert shown["decision"] == "BUY"
    assert len(shown["events"]) == 7


async def test_history_is_newest_first(api, session):
    await meeting(session, YESTERDAY)
    await meeting(session, TODAY)

    rows = (await api.get("/api/trading/sessions/history")).json()

    assert [r["session_date"] for r in rows] == [str(TODAY), str(YESTERDAY)]
    assert [r["decision"] for r in rows] == ["BUY", "BUY"]


async def test_sixth_click_in_a_day_is_limited(api):
    for _ in range(5):
        assert (await api.post(START)).status_code == 200

    assert (await api.post(START)).status_code == 429


async def price_now(session, value: int) -> None:
    session.add(
        MarketPrice(
            ts=datetime.now(UTC), symbol="BTCUSDT", price=Decimal(value), source="test"
        )
    )
    await session.commit()


async def test_summary_starts_at_100k_before_any_price(api):
    body = (await api.get("/api/trading/summary")).json()

    assert Decimal(body["value_usd"]) == Decimal(body["hold_usd"]) == 100_000
    assert body["last"] is None


async def test_summary_compares_the_team_with_holding(api, session):
    row = await meeting(session, YESTERDAY)
    session.add(
        PortfolioTrade(
            session_id=row.id,
            side="BUY",
            qty=Decimal("0.25"),
            price=Decimal(80_000),
            reason="test",
        )
    )
    await price_now(session, 88_000)

    body = (await api.get("/api/trading/summary")).json()

    # Team: 0.25 BTC gained 2,000 on 100,000; holding everything gained 10%.
    assert Decimal(body["value_usd"]) == 102_000
    assert Decimal(body["hold_usd"]) == 110_000
    assert body["last"]["decision"] == "BUY"
    assert len(body["last"]["events"]) == 7


async def test_summary_shows_todays_decision(api, session):
    await meeting(session, TODAY)
    await price_now(session, 80_000)

    body = (await api.get("/api/trading/summary")).json()

    assert body["today_status"] == "done"
    assert body["last"]["decision"] == "BUY"


async def test_summary_tells_when_todays_meeting_started(api, session):
    row = await meeting(session, TODAY)
    row.started_at = datetime(2026, 10, 28, 6, 30, tzinfo=UTC)
    await session.commit()

    body = (await api.get("/api/trading/summary")).json()

    assert body["today_started_at"].startswith("2026-10-28T06:30")
