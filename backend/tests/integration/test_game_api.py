from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx2
import pytest
from sqlalchemy import select

from app.config import get_settings
from app.db.models import (
    MarketPrice,
    Player,
    Prediction,
    SessionEvent,
    TradingSession,
)
from app.db.session import get_session
from app.game.api import NICKNAME_LIMITER, PREDICTION_LIMITER, live_price
from app.game.season import season_day
from app.game.settle import settle_predictions
from app.main import app
from app.security.cookie import sign
from app.trading.run import trading_day

NOW = datetime.now(UTC)
TODAY = trading_day(NOW)
YESTERDAY = TODAY - timedelta(days=1)
PRICE = Decimal(80_000)


@pytest.fixture
async def api(session):
    """HTTPS client (the cookie is Secure) with the test session and a fixed live price."""
    for limiter in (NICKNAME_LIMITER, PREDICTION_LIMITER):
        limiter.hits.clear()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[live_price] = lambda: PRICE
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="https://test") as c:
        yield c
    app.dependency_overrides.clear()


async def join(api, nickname: str = "satoshi") -> dict:
    response = await api.post("/api/game/players", json={"nickname": nickname})
    assert response.status_code == 201
    return response.json()


async def meeting(session, day, decision: str = "BUY") -> TradingSession:
    """A finished meeting with one spoken turn."""
    row = TradingSession(session_date=day, status="done", decision=decision)
    session.add(row)
    await session.flush()
    session.add(
        SessionEvent(
            session_id=row.id, seq=1, agent="data", kind="speech", text_en="Hi"
        )
    )
    await session.commit()
    return row


async def test_joining_gives_a_wallet_a_cookie_and_a_recovery_token(api):
    body = await join(api)

    assert body["nickname"] == "satoshi"
    assert Decimal(body["balance_usd"]) == 100_000
    assert body["today"] is None
    assert len(body["recovery_token"]) > 30
    assert "player" in api.cookies


async def test_a_player_cannot_join_twice(api):
    await join(api)
    response = await api.post("/api/game/players", json={"nickname": "other"})
    assert response.status_code == 409


async def test_nickname_is_unique_ignoring_case(api):
    await join(api)
    api.cookies.clear()
    response = await api.post("/api/game/players", json={"nickname": "SATOSHI"})
    assert response.status_code == 409
    assert response.json()["detail"] == "Nickname taken"


async def test_bad_nickname_is_rejected(api):
    response = await api.post("/api/game/players", json={"nickname": "admin_1"})
    assert response.status_code == 422


async def test_three_nicknames_per_ip_a_day_and_failures_do_not_count(api):
    await join(api)
    api.cookies.clear()
    await api.post("/api/game/players", json={"nickname": "satoshi"})
    for name in ("second", "third"):
        api.cookies.clear()
        await join(api, name)
    api.cookies.clear()
    response = await api.post("/api/game/players", json={"nickname": "fourth"})
    assert response.status_code == 429


async def test_predicting_needs_a_nickname(api):
    response = await api.post(
        "/api/game/predictions", json={"direction": "up", "stake_pct": 10}
    )
    assert response.status_code == 401


async def test_forged_cookie_is_not_a_player(api, session):
    await join(api)
    player = await session.scalar(select(Player))
    api.cookies.clear()
    api.cookies.set("player", f"{player.id}.forged")
    assert (await api.get("/api/game/me")).status_code == 401
    api.cookies.set("player", sign(player.id, get_settings()))
    assert (await api.get("/api/game/me")).status_code == 200


@pytest.mark.parametrize("stake", [0, 5, 15, 110])
async def test_stake_must_be_10_to_100_in_steps_of_10(api, stake):
    await join(api)
    response = await api.post(
        "/api/game/predictions", json={"direction": "up", "stake_pct": stake}
    )
    assert response.status_code == 422


async def test_one_prediction_a_day_at_the_live_price(api):
    await join(api)
    first = await api.post(
        "/api/game/predictions", json={"direction": "down", "stake_pct": 30}
    )
    second = await api.post(
        "/api/game/predictions", json={"direction": "up", "stake_pct": 10}
    )

    assert first.status_code == 201
    body = first.json()
    assert body["game_date"] == str(TODAY)
    assert Decimal(body["stake_usd"]) == 30_000
    assert Decimal(body["ref_price"]) == PRICE
    assert body["result"] is None
    assert second.status_code == 409
    me = (await api.get("/api/game/me")).json()
    assert me["today"]["direction"] == "down"


async def add_prediction(session, player, day, direction="up", stake=10_000, **kw):
    await session.flush()
    session.add(
        Prediction(
            player_id=player.id,
            game_date=day,
            direction=direction,
            stake_pct=10,
            stake_usd=Decimal(stake),
            ref_price=PRICE,
            **kw,
        )
    )
    await session.flush()


async def test_settling_pays_double_when_the_ai_was_wrong(session):
    player = Player(nickname="alice", balance_usd=Decimal(100_000))
    session.add(player)
    await meeting(session, YESTERDAY, decision="SELL")
    await add_prediction(session, player, YESTERDAY, "up")
    await add_prediction(session, player, TODAY, "up")

    settled = await settle_predictions(session, Decimal(81_000), NOW)

    assert settled == 1
    rows = {p.game_date: p for p in await session.scalars(select(Prediction))}
    assert rows[YESTERDAY].result == "win"
    assert rows[YESTERDAY].pnl_usd == Decimal("250.00")
    assert rows[TODAY].result is None
    await session.refresh(player)
    assert player.balance_usd == Decimal("100250.00")
    assert await settle_predictions(session, Decimal(90_000), NOW) == 0


@pytest.mark.parametrize("decision", ["HOLD", None])
async def test_no_bonus_when_the_ai_held_or_did_not_meet(session, decision):
    player = Player(nickname="bob", balance_usd=Decimal(100_000))
    session.add(player)
    if decision:
        await meeting(session, YESTERDAY, decision=decision)
    await add_prediction(session, player, YESTERDAY, "down")

    await settle_predictions(session, Decimal(79_200), NOW)

    await session.refresh(player)
    assert player.balance_usd == Decimal("100100.00")


async def test_a_loss_comes_out_of_the_wallet(session):
    player = Player(nickname="carol", balance_usd=Decimal(100_000))
    session.add(player)
    await meeting(session, YESTERDAY, decision="BUY")
    await add_prediction(session, player, YESTERDAY, "down")

    await settle_predictions(session, Decimal(81_000), NOW)

    await session.refresh(player)
    assert player.balance_usd == Decimal("99875.00")


async def test_me_shows_the_streak(api, session):
    await join(api)
    player = await session.scalar(select(Player))
    for days, result in [(3, "lose"), (2, "win"), (1, "win")]:
        await add_prediction(
            session, player, TODAY - timedelta(days=days), result=result, pnl_usd=0
        )

    me = (await api.get("/api/game/me")).json()
    assert me["streak"] == 2
    assert len(me["predictions"]) == 3


async def test_recovery_link_brings_the_player_to_a_new_device(api):
    token = (await join(api))["recovery_token"]
    api.cookies.clear()

    assert (
        await api.post("/api/game/recover", json={"token": "nope"})
    ).status_code == 404
    response = await api.post("/api/game/recover", json={"token": token})
    assert response.status_code == 200
    assert (await api.get("/api/game/me")).json()["nickname"] == "satoshi"


async def ranked_player(session, nickname, balance, pnls, first_day):
    """A player with one settled prediction per P&L, on days from first_day backwards."""
    player = Player(nickname=nickname, balance_usd=Decimal(balance))
    session.add(player)
    for i, pnl in enumerate(pnls):
        await add_prediction(
            session,
            player,
            first_day - timedelta(days=i),
            result="win",
            pnl_usd=Decimal(pnl),
        )


async def test_leaderboard_ranks_by_return_with_the_ai_team(api, session):
    session.add(MarketPrice(ts=NOW, symbol="BTCUSDT", price=PRICE, source="test"))
    start = season_day(NOW)
    # dana: +10% all time, 1,000 of it this month on 109,000 -> +0.92% this month.
    await ranked_player(session, "dana", 110_000, [1_000, 4_000, 5_000], start)
    await ranked_player(session, "erin", 95_000, [-5_000, 0, 0], start)
    await ranked_player(session, "frank", 200_000, [50_000, 50_000], start)
    await session.commit()

    month = (await api.get("/api/game/leaderboard")).json()
    ever = (await api.get("/api/game/leaderboard", params={"period": "all"})).json()

    assert [r["nickname"] for r in ever["rows"]] == ["dana", "AI Trading Team", "erin"]
    assert [r["return_pct"] for r in ever["rows"]] == [10.0, 0.0, -5.0]
    assert [r["rank"] for r in ever["rows"]] == [1, 2, 3]
    assert ever["rows"][1]["is_ai"] is True
    assert month["period"] == "month"
    assert month["rows"][0] == {
        "rank": 1,
        "nickname": "dana",
        "return_pct": 0.92,
        "predictions": 3,
        "is_ai": False,
    }
    assert month["rows"][2]["return_pct"] == -5.0


async def test_full_game_day(api, session):
    """Join, predict, settle the next morning, and climb the table after 3 days."""
    await meeting(session, TODAY, decision="BUY")
    session.add(MarketPrice(ts=NOW, symbol="BTCUSDT", price=PRICE, source="test"))
    await join(api)
    await api.post("/api/game/predictions", json={"direction": "down", "stake_pct": 50})
    player = await session.scalar(select(Player))
    for days in (1, 2):
        await add_prediction(
            session, player, TODAY - timedelta(days=days), result="draw", pnl_usd=0
        )

    tomorrow = NOW + timedelta(days=1)
    await settle_predictions(session, Decimal(78_400), tomorrow)

    me = (await api.get("/api/game/me")).json()
    assert me["predictions"][0]["result"] == "win"
    # 50,000 staked, 2% fall, AI said BUY: 1,000 doubled.
    assert Decimal(me["predictions"][0]["pnl_usd"]) == 2_000
    assert Decimal(me["balance_usd"]) == 102_000
    assert me["streak"] == 1
    board = (await api.get("/api/game/leaderboard", params={"period": "all"})).json()
    assert board["rows"][0]["nickname"] == "satoshi"
    assert board["rows"][0]["return_pct"] == 2.0
