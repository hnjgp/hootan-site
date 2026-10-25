"""Find the knowledge chunks closest in meaning to a question."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocChunk, Document
from app.llm.client import LLMClient

TOP_K = 5


@dataclass
class Hit:
    """One retrieved chunk; distance is cosine distance (0 = same meaning)."""

    content: str
    source: str
    title: str
    distance: float


async def search(
    session: AsyncSession,
    client: LLMClient,
    question: str,
    k: int = TOP_K,
    lang: str | None = None,
) -> list[Hit]:
    """Embed the question and return the k nearest chunks, nearest first.

    With lang, only chunks in that language are searched. Every knowledge file has
    both languages, and a Persian question given English chunks made the model
    translate company names wrongly (real test, 2026-10-25).
    """
    [vector] = await client.embed(session, [question])
    distance = DocChunk.embedding.cosine_distance(vector).label("distance")
    query = select(DocChunk.content, Document.source, Document.title, distance).join(
        Document
    )
    if lang:
        query = query.where(DocChunk.meta["lang"].astext == lang)
    rows = await session.execute(query.order_by(distance).limit(k))
    return [Hit(*row) for row in rows]
