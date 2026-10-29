import json
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.config import get_settings
from app.db.models import Position, SessionEvent, TradingSession
from app.exchange.book import Book, load_book, open_position
from app.llm.fake import FakeLLMClient
from app.trading.graph import run_meeting

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})
MARKET = {
    "price": 80000.0,
    "high_24h": 80900.0,
    "low_24h": 78850.0,
    "rsi_14": 39.4,
    "sma_7": 81074.0,
    "sma_30": 82736.0,
}
NEW = {
    "side": "long",
    "margin_pct": 100,
    "leverage": 10,
    "take_profit_pct": 4,
    "stop_loss_pct": 3,
}
TRADER = {"reason": "Oversold.", "positions": [], "new_position": NEW}
PM = {"reason": "Approved.", "approve": True}
FA = json.dumps({"text": "متن"})


async def new_session(session) -> TradingSession:
    row = TradingSession(session_date=date(2026, 10, 27), status="running")
    session.add(row)
    await session.commit()
    return row


async def events(session, row) -> list[SessionEvent]:
    query = select(SessionEvent).where(SessionEvent.session_id == row.id)
    return list(await session.scalars(query.order_by(SessionEvent.seq)))


async def test_full_meeting_records_every_speaker_and_trades_within_the_rules(
    session,
):
    row = await new_session(session)
    client = FakeLLMClient(
        SETTINGS,
        replies=[
            FA,
            FA,
            "Buy.",
            FA,
            "Wait.",
            FA,
            json.dumps(TRADER),
            FA,
            "Cut to 20%.",
            FA,
            json.dumps(PM),
            FA,
        ],
    )

    plan = await run_meeting(session, client, row, MARKET, Book())

    recorded = await events(session, row)
    assert [e.agent for e in recorded] == [
        "data", "news", "bull", "bear", "trader", "risk", "pm",
    ]  # fmt: skip
    assert [e.seq for e in recorded] == list(range(1, 8))
    assert [e.text_fa for e in recorded] == ["متن"] * 7
    assert recorded[0].payload == MARKET
    notes = recorded[5].payload["notes"]
    assert "5x limit" in notes[0] and "20% of equity" in notes[1]

    assert (plan.new.margin, plan.new.leverage) == (2_000, 5)
    assert (plan.new.tp_price, plan.new.sl_price) == (83_200, 77_600)
    position = await session.scalar(select(Position))
    assert (position.session_id, position.player_id, position.qty) == (
        row.id,
        None,
        Decimal("0.125"),
    )
    assert position.entry_price == 80_000
    assert (row.decision, row.qty) == ("LONG", Decimal("0.125"))


async def test_invalid_trader_reply_changes_nothing_without_asking_the_pm(session):
    """A failed translation leaves that line English and the meeting goes on."""
    row = await new_session(session)
    client = FakeLLMClient(
        SETTINGS,
        replies=[
            FA,
            FA,
            "Buy.",
            "not json",
            "Wait.",
            FA,
            "not json",
            FA,
            "Nothing to check.",
            FA,
            FA,
        ],
    )

    plan = await run_meeting(session, client, row, MARKET, Book())

    assert plan.empty
    assert client.replies == []
    assert len(client.calls) == 11
    assert await session.scalar(select(Position)) is None
    assert (row.decision, row.qty) == ("HOLD", None)
    recorded = await events(session, row)
    assert recorded[-1].agent == "pm"
    assert recorded[2].text_fa is None
    assert recorded[3].text_fa == "متن"


async def test_the_team_closes_an_open_position(session):
    old = await open_position(
        session, None, "short", Decimal(1_000), 2, Decimal(82_000)
    )
    await session.commit()
    row = await new_session(session)
    close = {"reason": "Turned.", "positions": [{"id": old.id, "action": "close"}]}
    client = FakeLLMClient(
        SETTINGS,
        replies=[
            FA,
            FA,
            "Up.",
            FA,
            "Down.",
            FA,
            json.dumps(close | {"new_position": None}),
            FA,
            "Fine.",
            FA,
            json.dumps(PM),
            FA,
        ],
    )

    plan = await run_meeting(
        session, client, row, MARKET, await load_book(session, None)
    )

    assert plan.close == [old.id]
    assert "#" in client.calls[2][-1]["content"]
    await session.refresh(old)
    assert (old.close_reason, old.close_price) == ("team", 80_000)
    assert (row.decision, row.qty) == ("CLOSE", None)
