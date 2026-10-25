import pytest
from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import DocChunk, Document
from app.llm.fake import FakeLLMClient, fake_vector
from app.twin.ingest import ingest

SETTINGS = get_settings().model_copy(update={"ai_enabled": True})


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


async def count(session, model):
    return await session.scalar(select(func.count(model.id)))


async def test_ingest_stores_documents_and_embedded_chunks(session, tmp_path):
    write(tmp_path, "resume_en.md", "# Resume\n## Skills\n- LangGraph\n")
    write(tmp_path, "projects/behengam.md", "# Behengam\n## فارسی\n- بهنگام\n")

    counts = await ingest(session, FakeLLMClient(SETTINGS), tmp_path)

    assert counts == {"projects/behengam.md": 1, "resume_en.md": 1}
    doc = await session.scalar(
        select(Document).where(Document.source == "resume_en.md")
    )
    assert (doc.title, doc.lang) == ("Resume", "en")
    chunk = await session.scalar(select(DocChunk).where(DocChunk.document_id == doc.id))
    assert chunk.content == "Resume | Skills\n- LangGraph"
    # pgvector stores 32-bit floats, so compare with float32 precision.
    assert list(chunk.embedding) == pytest.approx(fake_vector(chunk.content), rel=1e-6)
    assert chunk.meta == {"heading": "Skills", "lang": "en"}


async def test_reingest_replaces_instead_of_duplicating(session, tmp_path):
    write(tmp_path, "a.md", "# A\n## S\n- one\n")
    write(tmp_path, "b.md", "# B\n## S\n- two\n")
    client = FakeLLMClient(SETTINGS)
    await ingest(session, client, tmp_path)

    (tmp_path / "b.md").unlink()
    await ingest(session, client, tmp_path)

    assert await count(session, Document) == 1
    assert await count(session, DocChunk) == 1
