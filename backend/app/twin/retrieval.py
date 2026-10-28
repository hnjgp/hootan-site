"""Find the knowledge chunks that best answer a question: meaning plus exact words."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocChunk, Document
from app.llm.client import LLMClient
from app.twin.keyword import bm25_scores, rare_words, tokens

TOP_K = 5
# Reciprocal rank fusion constant; 60 is the usual choice from the original paper.
RRF_K = 60


@dataclass
class Hit:
    """One retrieved chunk; distance is cosine distance (0 = same meaning).

    rare_word: the chunk shares a rare word with the question (see keyword.py).
    """

    content: str
    source: str
    title: str
    distance: float
    rare_word: bool = False


def fuse(hits: list[Hit], keyword: list[float], k: int) -> list[Hit]:
    """Merge the meaning order (hits, nearest first) with keyword scores by RRF."""
    word_rank = sorted(
        (i for i, s in enumerate(keyword) if s > 0), key=lambda i: -keyword[i]
    )
    score = {i: 1 / (RRF_K + i + 1) for i in range(len(hits))}
    for rank, i in enumerate(word_rank, 1):
        score[i] += 1 / (RRF_K + rank)
    return [hits[i] for i in sorted(score, key=lambda i: -score[i])[:k]]


async def search(
    session: AsyncSession,
    client: LLMClient,
    question: str,
    k: int = TOP_K,
    lang: str | None = None,
) -> list[Hit]:
    """Embed the question and return the k best chunks by hybrid search.

    All chunks are ranked (the knowledge is about a hundred chunks), by vector
    distance and by BM25 on exact words, and the two orders are fused.
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
    hits = [Hit(*row) for row in await session.execute(query.order_by(distance))]
    if not hits:
        return []
    docs = [h.content for h in hits]
    best = fuse(hits, bm25_scores(question, docs), k)
    rare = rare_words(question, docs)
    for hit in best:
        hit.rare_word = bool(rare & set(tokens(hit.content)))
    return best
