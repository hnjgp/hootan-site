import json
from datetime import date
from decimal import Decimal

from sqlalchemy import select

from app.config import get_settings
from app.db.models import PortfolioTrade, SessionEvent, TradingSession
from app.llm.fake import FakeLLMClient
from app.trading.graph import run_meeting
from app.trading.portfolio import Portfolio

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})
MARKET = {
    "price": 80000.0,
    "high_24h": 80900.0,
    "low_24h": 78850.0,
    "rsi_14": 39.4,
    "sma_7": 81074.0,
    "sma_30": 82736.0,
}
TRADER = {"reason": "Oversold.", "action": "BUY", "size_pct": 100}
PM = {"reason": "Approved.", "approve": True, "stop_loss_pct": 3}


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
        replies=["Buy.", "Wait.", json.dumps(TRADER), "Cut to 20%.", json.dumps(PM)],
    )

    order = await run_meeting(session, client, row, MARKET, Portfolio())

    recorded = await events(session, row)
    assert [e.agent for e in recorded] == [
        "data", "news", "bull", "bear", "trader", "risk", "pm",
    ]  # fmt: skip
    assert [e.seq for e in recorded] == list(range(1, 8))
    assert recorded[0].payload == MARKET
    assert "20%" in recorded[5].payload["notes"][0]

    assert (order.action, order.qty, order.stop_price) == (
        "BUY",
        Decimal("0.25"),
        Decimal(77_600),
    )
    trade = await session.scalar(select(PortfolioTrade))
    assert (trade.session_id, trade.qty, trade.price) == (
        row.id,
        Decimal("0.25"),
        Decimal(80_000),
    )
    assert (row.decision, row.qty) == ("BUY", Decimal("0.25"))


async def test_invalid_trader_reply_holds_without_asking_the_pm(session):
    row = await new_session(session)
    client = FakeLLMClient(
        SETTINGS, replies=["Buy.", "Wait.", "not json", "Nothing to check."]
    )

    order = await run_meeting(session, client, row, MARKET, Portfolio())

    assert order.action == "HOLD"
    assert client.replies == []
    assert len(client.calls) == 4
    assert await session.scalar(select(PortfolioTrade)) is None
    assert (row.decision, row.qty) == ("HOLD", None)
    assert (await events(session, row))[-1].agent == "pm"
