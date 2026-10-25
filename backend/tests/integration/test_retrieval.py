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
