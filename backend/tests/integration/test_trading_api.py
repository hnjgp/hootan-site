from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx2
import pytest
from sqlalchemy import func, select

from app.db.models import SessionEvent, TradingSession
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
    """A recorded BUY meeting; the last three events are secret."""
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
                is_secret=seq > 4,
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


async def test_todays_meeting_hides_secrets_and_the_decision(api, session):
    await meeting(session, TODAY)

    shown = (await api.get(TODAY_URL)).json()["session"]

    assert shown["session_date"] == str(TODAY)
    assert (shown["decision"], shown["qty"]) == (None, None)
    events = shown["events"]
    assert [e["agent"] for e in events] == AGENTS
    assert [e["hidden"] for e in events] == [False] * 4 + [True] * 3
    assert "text_en" not in events[4]
    assert events[2]["text_en"] == "bull speaks"


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
    assert all(not e["hidden"] for e in shown["events"])


async def test_history_is_newest_first_with_todays_decision_hidden(api, session):
    await meeting(session, YESTERDAY)
    await meeting(session, TODAY)

    rows = (await api.get("/api/trading/sessions/history")).json()

    assert [r["session_date"] for r in rows] == [str(TODAY), str(YESTERDAY)]
    assert [r["decision"] for r in rows] == [None, "BUY"]


async def test_sixth_click_in_a_day_is_limited(api):
    for _ in range(5):
        assert (await api.post(START)).status_code == 200

    assert (await api.post(START)).status_code == 429
