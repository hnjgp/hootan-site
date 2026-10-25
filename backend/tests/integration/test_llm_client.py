from decimal import Decimal

import pytest
from sqlalchemy import select

from app.config import get_settings
from app.db.models import EMBED_DIM, LLMUsage
from app.llm.budget import BudgetExceeded
from app.llm.fake import FakeLLMClient

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})
MESSAGES = [{"role": "user", "content": "hi"}]


async def test_chat_returns_reply_and_records_cost(session):
    client = FakeLLMClient(SETTINGS, replies=["hello"])

    reply = await client.chat(session, "trading", "gpt-5-nano", MESSAGES, 250)

    assert reply == "hello"
    assert client.calls == [MESSAGES]
    usage = (await session.scalars(select(LLMUsage))).one()
    assert (usage.feature, usage.tokens_in, usage.tokens_out) == ("trading", 100, 50)
    assert usage.cost_usd == Decimal("0.000025")


async def test_no_call_when_budget_is_off(session):
    off = SETTINGS.model_copy(update={"ai_enabled": False})
    client = FakeLLMClient(off, replies=["hello"])

    with pytest.raises(BudgetExceeded):
        await client.chat(session, "twin", "gpt-5-nano", MESSAGES, 400)

    assert client.calls == []
    assert (await session.scalars(select(LLMUsage))).all() == []


async def test_stream_yields_pieces_then_completion_and_records_cost(session):
    client = FakeLLMClient(SETTINGS, replies=["Hootan builds agents"])

    items = [
        item
        async for item in client.stream_chat(
            session, "twin", "gemini-2.5-flash-lite", MESSAGES, 400
        )
    ]

    pieces, completion = items[:-1], items[-1]
    assert "".join(pieces) == "Hootan builds agents"
    assert completion.text == "Hootan builds agents"
    assert completion.cost_usd == Decimal("0.000030")
    usage = (await session.scalars(select(LLMUsage))).one()
    assert (usage.feature, usage.model) == ("twin", "gemini-2.5-flash-lite")


async def test_stream_not_started_when_budget_is_off(session):
    off = SETTINGS.model_copy(update={"ai_enabled": False})
    client = FakeLLMClient(off, replies=["hello"])

    with pytest.raises(BudgetExceeded):
        async for _ in client.stream_chat(session, "twin", "gpt-5-nano", MESSAGES, 400):
            pass

    assert client.calls == []


async def test_embed_returns_one_vector_per_text_and_records_usage(session):
    client = FakeLLMClient(SETTINGS)

    vectors = await client.embed(session, ["a", "b", "a"])

    assert len(vectors) == 3
    assert len(vectors[0]) == EMBED_DIM
    assert vectors[0] == vectors[2] != vectors[1]
    usage = (await session.scalars(select(LLMUsage))).one()
    assert (usage.feature, usage.model, usage.tokens_in) == (
        "embedding",
        "text-embedding-3-small",
        30,
    )
