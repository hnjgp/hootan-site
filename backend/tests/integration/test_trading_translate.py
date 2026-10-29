import json

from app.config import get_settings
from app.llm.fake import FakeLLMClient
from app.trading.translate import translate_line

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})


def fa(text: str) -> str:
    return json.dumps({"text": text})


async def test_line_is_translated_with_earlier_lines_as_context(session):
    client = FakeLLMClient(SETTINGS, replies=[fa("صبر کن.")])

    text = await translate_line(session, client, "Wait.", [("Buy now.", "الان بخر.")])

    assert text == "صبر کن."
    sent = client.calls[0]
    assert [m["role"] for m in sent] == ["system", "user", "assistant", "user"]
    assert sent[1]["content"] == "Buy now."
    assert json.loads(sent[2]["content"]) == {"text": "الان بخر."}
    assert sent[3]["content"] == "Wait."
    assert client.extra["timeout"] == 10


async def test_bad_reply_gives_no_translation(session):
    client = FakeLLMClient(SETTINGS, replies=["not json"])

    assert await translate_line(session, client, "Wait.", []) is None


async def test_english_copied_back_is_rejected(session):
    """gpt-5-nano did this in a real call: the reply had no translation."""
    client = FakeLLMClient(SETTINGS, replies=[fa("Wait.")])

    assert await translate_line(session, client, "Wait.", []) is None


async def test_budget_reached_skips_translation(session):
    off = SETTINGS.model_copy(update={"ai_enabled": False})
    client = FakeLLMClient(off, replies=[])

    assert await translate_line(session, client, "Wait.", []) is None
