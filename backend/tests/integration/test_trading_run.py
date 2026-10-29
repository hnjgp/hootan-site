import json
from datetime import UTC, date, datetime

from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import Position, SessionEvent, TradingSession
from app.llm.fake import FakeLLMClient
from app.market.prices import PriceUnavailable
from app.trading.run import (
    claim_scheduled,
    fail_stale,
    get_or_create,
    hold_meeting,
    trading_day,
)

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})
DAY = date(2026, 10, 27)
MARKET = {
    "price": 80000.0,
    "high_24h": 80900.0,
    "low_24h": 78850.0,
    "rsi_14": 39.4,
    "sma_7": 81074.0,
    "sma_30": 82736.0,
}
FA = json.dumps({"text": "متن"})
REPLIES = [
    FA,
    FA,
    "Buy.",
    FA,
    "Wait.",
    FA,
    json.dumps(
        {
            "reason": "Oversold.",
            "positions": [],
            "new_position": {
                "side": "long",
                "margin_pct": 10,
                "leverage": 2,
                "take_profit_pct": 0,
                "stop_loss_pct": 5,
            },
        }
    ),
    FA,
    "Within limits.",
    FA,
    json.dumps({"reason": "Approved.", "approve": True}),
    FA,
]


async def fixed_market(db) -> dict:
    return MARKET


async def no_price(db) -> dict:
    raise PriceUnavailable


async def count(session, model) -> int:
    return await session.scalar(select(func.count()).select_from(model))


def test_trading_day_starts_at_nine_tehran():
    # 08:59 and 09:00 Tehran (UTC+3:30) on 2026-10-27
    assert trading_day(datetime(2026, 10, 27, 5, 29, tzinfo=UTC)) == date(2026, 10, 26)
    assert trading_day(datetime(2026, 10, 27, 5, 30, tzinfo=UTC)) == date(2026, 10, 27)


async def test_second_create_on_the_same_day_returns_the_same_row(session):
    first, created = await get_or_create(session, DAY, "scheduled")
    second, created_again = await get_or_create(session, DAY, "scheduled")

    assert (created, created_again) == (True, False)
    assert first.id == second.id
    assert await count(session, TradingSession) == 1


async def test_worker_claims_a_queued_meeting_once(session):
    row, _ = await get_or_create(session, DAY, "scheduled")

    claimed = await claim_scheduled(session)
    again = await claim_scheduled(session)

    assert [r.id for r in claimed] == [row.id]
    assert claimed[0].status == "running"
    assert claimed[0].started_at is not None
    assert again == []


async def test_only_meetings_running_too_long_are_failed(session):
    now = datetime(2026, 10, 27, 12, 0, tzinfo=UTC)
    old, _ = await get_or_create(session, DAY, "running")
    fresh, _ = await get_or_create(session, date(2026, 10, 28), "running")
    old.started_at = datetime(2026, 10, 27, 11, 49, tzinfo=UTC)
    fresh.started_at = datetime(2026, 10, 27, 11, 55, tzinfo=UTC)
    await session.commit()

    assert await fail_stale(session, now) == 1

    await session.refresh(old)
    await session.refresh(fresh)
    assert (old.status, fresh.status) == ("failed", "running")


async def test_meeting_ends_done_with_trade_and_persian_text(session):
    row, _ = await get_or_create(session, DAY, "scheduled")
    client = FakeLLMClient(SETTINGS, replies=list(REPLIES))

    row = await hold_meeting(session, client, row, load_market=fixed_market)

    assert row.status == "done"
    assert row.decision == "LONG"
    assert row.started_at <= row.finished_at
    assert await count(session, Position) == 1
    texts = await session.scalars(select(SessionEvent.text_fa))
    assert list(texts) == ["متن"] * 7


async def test_budget_used_up_skips_the_meeting(session):
    row, _ = await get_or_create(session, DAY, "scheduled")
    client = FakeLLMClient(SETTINGS.model_copy(update={"ai_enabled": False}))

    row = await hold_meeting(session, client, row, load_market=fixed_market)

    assert row.status == "skipped"
    assert await count(session, SessionEvent) == 0


async def test_price_outage_fails_the_meeting_without_trading(session):
    row, _ = await get_or_create(session, DAY, "scheduled")
    client = FakeLLMClient(SETTINGS, replies=list(REPLIES))

    row = await hold_meeting(session, client, row, load_market=no_price)

    assert row.status == "failed"
    assert row.finished_at is not None
    assert await count(session, Position) == 0
