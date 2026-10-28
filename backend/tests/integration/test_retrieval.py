import pytest

from app.config import get_settings
from app.llm.fake import FakeLLMClient
from app.twin.ingest import ingest
from app.twin.retrieval import search

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})


async def test_search_returns_nearest_chunks_first(session, tmp_path):
    (tmp_path / "resume_en.md").write_text(
        "# Resume\n## Skills\n- LangGraph\n## Education\n- M.Sc. AI\n## Hobbies\n- Chess\n",
        encoding="utf-8",
    )
    client = FakeLLMClient(SETTINGS)
    await ingest(session, client, tmp_path)

    # Fake vectors are equal only for equal texts, so this question matches one chunk.
    hits = await search(session, client, "Resume | Education\n- M.Sc. AI", k=2)

    assert len(hits) == 2
    assert hits[0].content == "Resume | Education\n- M.Sc. AI"
    assert (hits[0].source, hits[0].title) == ("resume_en.md", "Resume")
    assert hits[0].distance == pytest.approx(0, abs=1e-6)
    assert hits[1].distance > hits[0].distance


async def test_exact_word_lifts_a_chunk_the_meaning_search_missed(session, tmp_path):
    (tmp_path / "learning.md").write_text(
        "# Skills\n## Python\n- pandas\n## Power BI\n- DAX\n## Automation\n- n8n\n",
        encoding="utf-8",
    )
    client = FakeLLMClient(SETTINGS)
    await ingest(session, client, tmp_path)

    # Fake vectors give no meaning, so only the word "automation" can find the chunk.
    hits = await search(session, client, "Any automation experience?", k=1)

    assert hits[0].content == "Skills | Automation\n- n8n"


async def test_search_can_keep_only_one_language(session, tmp_path):
    (tmp_path / "resume.md").write_text(
        "# Resume\n## Experience\n- Cafe Bazaar\n## سوابق کاری\n- کافه‌بازار\n",
        encoding="utf-8",
    )
    client = FakeLLMClient(SETTINGS)
    await ingest(session, client, tmp_path)

    # The question matches the English chunk exactly, but only Persian is allowed.
    hits = await search(
        session, client, "Resume | Experience\n- Cafe Bazaar", lang="fa"
    )

    assert [h.content for h in hits] == ["Resume | سوابق کاری\n- کافه‌بازار"]
