from decimal import Decimal

import pytest
from sqlalchemy import select

from app.config import get_settings
from app.db.models import LLMUsage
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
