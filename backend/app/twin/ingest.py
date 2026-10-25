"""Load the Markdown files in knowledge/ into documents and doc_chunks.

Run from backend/: uv run python -m app.twin.ingest
Every run re-embeds all files and removes documents whose file is gone.
"""

import asyncio
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import DocChunk, Document
from app.db.session import SessionLocal
from app.llm.client import LLMClient
from app.twin.chunking import chunk_markdown

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"


def doc_lang(langs: set[str]) -> str:
    """'fa', 'en' or 'both' depending on the languages of a document's chunks."""
    return langs.pop() if len(langs) == 1 else "both"


async def ingest(
    session: AsyncSession, client: LLMClient, root: Path
) -> dict[str, int]:
    """Replace all documents with the Markdown files under root; return chunk counts."""
    files = sorted(root.rglob("*.md"))
    parsed = {
        f.relative_to(root).as_posix(): chunk_markdown(f.read_text("utf-8"))
        for f in files
    }
    texts = [c.content for _, chunks in parsed.values() for c in chunks]
    vectors = iter(await client.embed(session, texts))

    await session.execute(delete(Document))
    for source, (title, chunks) in parsed.items():
        doc = Document(
            title=title or source,
            source=source,
            lang=doc_lang({c.lang for c in chunks}),
        )
        session.add(doc)
        await session.flush()
        session.add_all(
            DocChunk(
                document_id=doc.id,
                content=c.content,
                embedding=next(vectors),
                meta={"heading": c.heading, "lang": c.lang},
            )
            for c in chunks
        )
    await session.commit()
    return {source: len(chunks) for source, (_, chunks) in parsed.items()}


async def main() -> None:
    """Ingest the real knowledge folder with the real provider and print counts."""
    async with SessionLocal() as session:
        counts = await ingest(session, LLMClient(get_settings()), KNOWLEDGE_DIR)
    for source, n in counts.items():
        print(f"{source}: {n} chunks")
    print(f"total: {sum(counts.values())} chunks")


if __name__ == "__main__":
    asyncio.run(main())
