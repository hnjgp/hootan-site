import json

import httpx2
import pytest
from sqlalchemy import select

from app.config import get_settings
from app.db.models import ChatLog, Lead, Player
from app.db.session import get_session
from app.llm.client import get_llm_client
from app.llm.fake import FakeLLMClient
from app.main import app
from app.security.cookie import sign
from app.twin.api import CHAT_LIMITERS, LEAD_LIMITERS
from app.twin.ingest import ingest
from app.twin.prompt import HANDOFF

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})
# Fake vectors match only identical text, so asking a chunk's exact content finds it.
CHUNK = "Resume | Education\n- M.Sc. AI at Amirkabir University"


@pytest.fixture
async def api(session, tmp_path):
    """HTTP client on the app with the test session, a fake LLM and fresh limits."""
    (tmp_path / "resume_en.md").write_text(
        "# Resume\n## Education\n- M.Sc. AI at Amirkabir University\n", encoding="utf-8"
    )
    fake = FakeLLMClient(SETTINGS)
    await ingest(session, fake, tmp_path)
    for limiter in CHAT_LIMITERS + LEAD_LIMITERS:
        limiter.hits.clear()

    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_llm_client] = lambda: fake
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as c:
        c.fake = fake
        yield c
    app.dependency_overrides.clear()


def parse(body: str) -> list[tuple[str, object]]:
    """Turn an SSE body into (event, data) pairs."""
    events = []
    for block in body.strip().split("\n\n"):
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        events.append((fields["event"], json.loads(fields["data"])))
    return events


async def chat(api, question: str) -> list[tuple[str, object]]:
    response = await api.post("/api/twin/chat", json={"question": question})
    assert response.status_code == 200
    return parse(response.text)


async def test_answer_streams_tokens_then_sources_and_is_logged(api, session):
    api.fake.replies = ["Hootan studied AI at Amirkabir University."]

    events = await chat(api, CHUNK)

    names = [name for name, _ in events]
    assert names[0] == "status" and names[-2:] == ["sources", "done"]
    assert "answering" in [d.get("state") for n, d in events if n == "status"]
    text = "".join(d["text"] for n, d in events if n == "token")
    assert text == "Hootan studied AI at Amirkabir University."
    assert dict(events)["sources"] == [{"file": "resume_en.md", "title": "Resume"}]
    log = await session.scalar(select(ChatLog))
    assert (log.question, log.answer, log.tokens_in) == (CHUNK, text, 100)


async def test_far_question_hands_off_without_calling_the_model(api):
    events = await chat(api, "Who won the last World Cup?")

    assert [n for n, _ in events][-2:] == ["handoff", "done"]
    assert "email" in dict(events)["handoff"]["message"]
    assert api.fake.calls == []


async def test_model_handoff_marker_is_never_shown(api, session):
    api.fake.replies = [HANDOFF]

    events = await chat(api, CHUNK)

    assert "token" not in [n for n, _ in events]
    assert "handoff" in dict(events)
    log = await session.scalar(select(ChatLog))
    assert HANDOFF not in log.answer


async def test_persian_question_gets_persian_handoff(api):
    events = await chat(api, "غذای مورد علاقه‌ات چیست؟")

    assert "ایمیل" in dict(events)["handoff"]["message"]


async def test_fallback_when_ai_is_off(api):
    api.fake.settings = SETTINGS.model_copy(update={"ai_enabled": False})

    events = await chat(api, CHUNK)

    assert [n for n, _ in events] == ["status", "fallback", "done"]


async def test_too_long_question_is_rejected(api):
    response = await api.post("/api/twin/chat", json={"question": "x" * 501})

    assert response.status_code == 422


async def test_eleventh_question_in_a_day_is_limited(api):
    lefts = [
        dict(await chat(api, "Who won the last World Cup?"))["done"]["left"]
        for _ in range(10)
    ]

    response = await api.post("/api/twin/chat", json={"question": "again"})

    assert lefts == list(range(9, -1, -1))
    assert response.status_code == 429


async def test_lead_is_stored(api, session):
    response = await api.post(
        "/api/leads", json={"email": "hr@example.com", "question": "Salary?"}
    )

    assert response.status_code == 201
    lead = await session.scalar(select(Lead))
    assert (lead.email, lead.context) == ("hr@example.com", "Salary?")


async def test_sixth_lead_in_a_day_is_limited(api):
    body = {"email": "hr@example.com", "question": "Salary?"}
    for _ in range(5):
        assert (await api.post("/api/leads", json=body)).status_code == 201

    response = await api.post("/api/leads", json=body)

    assert response.status_code == 429


async def test_invalid_lead_email_is_rejected(api):
    response = await api.post("/api/leads", json={"email": "abc@", "question": "q"})

    assert response.status_code == 422


async def test_a_logged_in_visitor_is_shown_beside_the_question_in_the_admin_panel(
    api, session, monkeypatch
):
    player = Player(nickname="visitor", email="v@b.com")
    session.add(player)
    await session.commit()
    api.fake.replies = ["Hootan studied AI at Amirkabir University."]
    cookie = {"Cookie": f"player={sign(player.id, get_settings())}"}

    await api.post("/api/twin/chat", json={"question": CHUNK}, headers=cookie)

    assert (await session.scalar(select(ChatLog))).player_id == player.id
    monkeypatch.setattr(get_settings(), "admin_token", "secret")
    (listed,) = (
        await api.get("/api/admin/chats", headers={"X-Admin-Token": "secret"})
    ).json()
    assert (listed["nickname"], listed["email"], listed["question"]) == (
        "visitor",
        "v@b.com",
        CHUNK,
    )
