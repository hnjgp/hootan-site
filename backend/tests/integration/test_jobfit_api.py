import json

import httpx2
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import JobFitRequest, LLMUsage
from app.db.session import get_session
from app.jobfit.api import JOBFIT_LIMITERS
from app.llm.client import get_llm_client
from app.llm.fake import FakeLLMClient
from app.main import app
from app.twin.ingest import ingest

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})
AD = "AI Engineer: build RAG pipelines and LangGraph agents with Python and FastAPI."
REPLY = {
    "requirements": [
        {
            "requirement": "RAG",
            "kind": "skill",
            "must_have": True,
            "status": "met",
            "note": "Astra",
        },
        {
            "requirement": "2 years",
            "kind": "experience",
            "must_have": True,
            "status": "missing",
            "note": "",
        },
    ],
    "strengths": [{"point": "RAG", "evidence": "Astra"}],
    "gaps": ["Two years in an AI role"],
    "summary": "Strong skill match.",
    "questions": ["Q1", "Q2", "Q3"],
    "score": 82,
}


@pytest.fixture
async def api(session, tmp_path):
    """HTTP client on the app with one English and one Persian knowledge file."""
    (tmp_path / "resume_en.md").write_text(
        "# Resume\n## Skills\n- RAG with pgvector in Astra\n", encoding="utf-8"
    )
    (tmp_path / "resume_fa.md").write_text(
        "# رزومه\n## مهارت‌ها\n- ساخت RAG در پروژه‌ی Astra\n", encoding="utf-8"
    )
    fake = FakeLLMClient(SETTINGS)
    await ingest(session, fake, tmp_path)
    for limiter in JOBFIT_LIMITERS:
        limiter.hits.clear()

    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_llm_client] = lambda: fake
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="http://test") as c:
        c.fake = fake
        yield c
    app.dependency_overrides.clear()


async def post(api, lang: str = "en"):
    return await api.post("/api/jobfit", json={"job_ad": AD, "lang": lang})


async def test_result_is_banded_returned_and_stored(api, session):
    api.fake.replies = [json.dumps(REPLY)]

    response = await post(api)

    assert response.status_code == 200
    body = response.json()
    # Every must-have skill is met and missing experience is ignored: lifted to 90.
    assert body["score"] == 90
    assert body["gaps"] == ["Two years in an AI role"]
    row = await session.scalar(select(JobFitRequest))
    assert (row.score, row.lang, row.jd_text) == (90, "en", AD)
    assert row.result["score"] == 90
    assert row.model == SETTINGS.model_jobfit and row.cost_usd > 0


async def test_model_sees_only_the_english_profile_and_the_ad(api):
    api.fake.replies = [json.dumps(REPLY)]

    await post(api, lang="fa")

    system, user = (m["content"] for m in api.fake.calls[0])
    assert "RAG with pgvector in Astra" in system
    assert "ساخت" not in system
    assert f"<job_ad>\n{AD}\n</job_ad>" in user
    assert "Persian" in user


async def test_ai_off_answers_503_without_a_call(api, session):
    api.fake.settings = SETTINGS.model_copy(update={"ai_enabled": False})

    response = await post(api, lang="fa")

    assert response.status_code == 503
    assert "موقتاً خاموش" in response.json()["detail"]
    assert api.fake.calls == []
    assert await session.scalar(select(func.count(JobFitRequest.id))) == 0


async def test_sixth_request_in_a_day_is_limited(api):
    api.fake.replies = [json.dumps(REPLY)] * 5
    for _ in range(5):
        assert (await post(api)).status_code == 200

    assert (await post(api)).status_code == 429


async def test_too_long_ad_is_rejected(api):
    response = await api.post("/api/jobfit", json={"job_ad": "x" * 6001, "lang": "en"})
    assert response.status_code == 422


async def test_invalid_model_reply_is_not_returned_but_its_cost_is_recorded(
    api, session
):
    api.fake.replies = [json.dumps(REPLY | {"score": 150})]

    with pytest.raises(ValidationError):
        await post(api)

    usage = await session.scalar(
        select(func.count(LLMUsage.id)).where(LLMUsage.feature == "jobfit")
    )
    assert usage == 1
    assert await session.scalar(select(func.count(JobFitRequest.id))) == 0
