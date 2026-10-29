from datetime import date

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    EMBED_DIM,
    DocChunk,
    Document,
    EquitySnapshot,
    Player,
    TradingSession,
)

DAY = date(2026, 10, 25)


def axis(i: int) -> list[float]:
    """Unit vector along dimension i."""
    v = [0.0] * EMBED_DIM
    v[i] = 1.0
    return v


async def test_insert_and_read_player(session):
    session.add(Player(nickname="hootan"))
    await session.commit()

    player = await session.scalar(select(Player).where(Player.nickname == "hootan"))
    assert player.id is not None
    assert player.created_at is not None


async def test_rollback_isolates_tests(session):
    assert await session.scalar(select(Player)) is None


async def test_nickname_is_unique(session):
    session.add(Player(nickname="same"))
    await session.flush()
    session.add(Player(nickname="same"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_one_snapshot_per_owner_and_day_even_for_the_team(session):
    for _ in range(2):
        session.add(EquitySnapshot(day=DAY, player_id=None, equity_usd=1, price=1))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_emails_are_unique_ignoring_case(session):
    session.add(Player(nickname="a", email="x@y.com"))
    await session.flush()
    session.add(Player(nickname="b", email="X@y.com"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_one_trading_session_per_day(session):
    session.add(TradingSession(session_date=DAY, status="running"))
    await session.flush()
    session.add(TradingSession(session_date=DAY, status="running"))
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_nearest_chunk_by_cosine_distance(session):
    doc = Document(title="Resume", source="resume_en.md", lang="en")
    session.add(doc)
    await session.flush()
    session.add_all(
        [
            DocChunk(document_id=doc.id, content="far", embedding=axis(0)),
            DocChunk(document_id=doc.id, content="near", embedding=axis(1)),
        ]
    )
    await session.flush()

    query = [0.0] * EMBED_DIM
    query[0], query[1] = 0.1, 0.9
    nearest = await session.scalar(
        select(DocChunk.content).order_by(DocChunk.embedding.cosine_distance(query))
    )
    assert nearest == "near"


async def test_deleting_document_deletes_its_chunks(session):
    doc = Document(title="FAQ", source="faq_en.md", lang="en")
    session.add(doc)
    await session.flush()
    session.add(DocChunk(document_id=doc.id, content="x", embedding=axis(0)))
    await session.flush()

    await session.execute(delete(Document).where(Document.id == doc.id))
    assert await session.scalar(select(func.count(DocChunk.id))) == 0
