from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import Player, Prediction, TradingSession

DAY = date(2026, 10, 25)


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


async def test_one_prediction_per_player_per_day(session):
    player = Player(nickname="p1")
    session.add(player)
    await session.flush()
    for _ in range(2):
        session.add(
            Prediction(
                player_id=player.id,
                game_date=DAY,
                direction="up",
                stake=10,
                ref_price=Decimal("100000.00"),
            )
        )
    with pytest.raises(IntegrityError):
        await session.flush()


async def test_one_trading_session_per_day(session):
    session.add(TradingSession(session_date=DAY, status="running"))
    await session.flush()
    session.add(TradingSession(session_date=DAY, status="running"))
    with pytest.raises(IntegrityError):
        await session.flush()
