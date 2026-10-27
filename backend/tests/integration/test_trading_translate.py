import json
from datetime import date

from sqlalchemy import select

from app.config import get_settings
from app.db.models import SessionEvent, TradingSession
from app.llm.fake import FakeLLMClient
from app.trading.translate import translate_session

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})


async def session_with_events(session, texts: list[str]) -> TradingSession:
    row = TradingSession(session_date=date(2026, 10, 27), status="done")
    session.add(row)
    await session.flush()
    for seq, text in enumerate(texts, start=1):
        session.add(
            SessionEvent(
                session_id=row.id, seq=seq, agent="bull", kind="speech", text_en=text
            )
        )
    await session.commit()
    return row


async def persian(session, row) -> list[str | None]:
    query = select(SessionEvent.text_fa).where(SessionEvent.session_id == row.id)
    return list(await session.scalars(query.order_by(SessionEvent.seq)))


async def test_every_event_gets_its_persian_text_in_order(session):
    row = await session_with_events(session, ["Buy now.", "Wait."])
    reply = json.dumps({"texts": ["الان بخر.", "صبر کن."]})
    client = FakeLLMClient(SETTINGS, replies=[reply])

    assert await translate_session(session, client, row.id)

    assert await persian(session, row) == ["الان بخر.", "صبر کن."]
    assert json.loads(client.calls[0][1]["content"]) == ["Buy now.", "Wait."]


async def test_wrong_count_or_bad_reply_leaves_persian_empty(session):
    row = await session_with_events(session, ["Buy now.", "Wait."])
    short = json.dumps({"texts": ["الان بخر."]})
    client = FakeLLMClient(SETTINGS, replies=[short, "not json"])

    assert not await translate_session(session, client, row.id)
    assert not await translate_session(session, client, row.id)

    assert await persian(session, row) == [None, None]


async def test_english_copied_back_is_rejected(session):
    """gpt-5-nano did this in a real call: right count, no translation."""
    row = await session_with_events(session, ["Buy now.", "Wait."])
    copy = json.dumps({"texts": ["Buy now.", "صبر کن."]})
    client = FakeLLMClient(SETTINGS, replies=[copy])

    assert not await translate_session(session, client, row.id)
    assert await persian(session, row) == [None, None]


async def test_budget_reached_skips_translation(session):
    row = await session_with_events(session, ["Buy now."])
    off = SETTINGS.model_copy(update={"ai_enabled": False})
    client = FakeLLMClient(off, replies=[])

    assert not await translate_session(session, client, row.id)
    assert await persian(session, row) == [None]
