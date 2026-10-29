from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx2
import pytest
from sqlalchemy import select

from app.config import get_settings
from app.db.models import (
    MarketPrice,
    Player,
    PortfolioTrade,
    Prediction,
    SessionEvent,
    TradingSession,
)
from app.db.session import get_session
from app.game import api as game_api
from app.game.accounts import JPEG, LOGIN_LIMITER, SIGNUP_LIMITER
from app.game.api import PREDICTION_LIMITER, live_price
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
    for limiter in (SIGNUP_LIMITER, LOGIN_LIMITER, PREDICTION_LIMITER):
        limiter.hits.clear()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[live_price] = lambda: PRICE
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="https://test") as c:
        yield c
    app.dependency_overrides.clear()


async def join(api, nickname: str = "satoshi", **extra) -> dict:
    body = {"nickname": nickname, "password": "pw", "email": "a@b.com"} | extra
    response = await api.post("/api/game/players", json=body)
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


async def test_signing_up_stores_the_account_and_logs_in(api, session):
    body = await join(api, email="a@b.com", phone="+98 912 000 0000")

    assert body["nickname"] == "satoshi"
    assert Decimal(body["balance_usd"]) == 100_000
    assert body["today"] is None
    assert body["avatar"] is False
    assert "player" in api.cookies
    player = await session.scalar(select(Player))
    assert (player.password, player.email, player.phone) == (
        "pw",
        "a@b.com",
        "+98 912 000 0000",
    )


@pytest.mark.parametrize(
    "extra",
    [
        {"email": "not-an-email"},
        {"email": None},
        {"phone": "call me"},
        {"password": ""},
        {"nickname": " "},
        {"nickname": "x" * 21},
    ],
)
async def test_bad_email_phone_password_or_nickname_length_is_rejected(api, extra):
    body = {"nickname": "satoshi", "password": "pw", "email": "a@b.com"} | extra
    response = await api.post("/api/game/players", json=body)
    assert response.status_code == 422


async def test_log_out_then_log_in_with_the_password(api):
    await join(api)
    assert (await api.post("/api/game/logout")).status_code == 204
    assert (await api.get("/api/game/me")).status_code == 401

    wrong = await api.post(
        "/api/game/login", json={"nickname": "satoshi", "password": "nope"}
    )
    assert wrong.status_code == 401
    right = await api.post(
        "/api/game/login", json={"nickname": "Satoshi", "password": "pw"}
    )
    assert right.status_code == 200
    assert (await api.get("/api/game/me")).json()["nickname"] == "satoshi"


async def test_twenty_login_tries_an_hour(api):
    await join(api)
    for _ in range(20):
        await api.post("/api/game/login", json={"nickname": "x", "password": "y"})
    response = await api.post(
        "/api/game/login", json={"nickname": "satoshi", "password": "pw"}
    )
    assert response.status_code == 429


async def test_profile_photo_is_a_small_jpeg(api):
    await join(api)
    jpeg = JPEG + b"0" * 100
    assert (await api.get("/api/game/me/avatar")).status_code == 404
    assert (await api.put("/api/game/me/avatar", content=b"<svg>")).status_code == 422
    assert (
        await api.put("/api/game/me/avatar", content=jpeg + b"0" * 100_000)
    ).status_code == 422
    assert (await api.put("/api/game/me/avatar", content=jpeg)).status_code == 204

    photo = await api.get("/api/game/me/avatar")
    assert photo.content == jpeg
    assert photo.headers["content-type"] == "image/jpeg"
    assert (await api.get("/api/game/me")).json()["avatar"] is True


async def test_nickname_is_unique_ignoring_case(api):
    await join(api)
    api.cookies.clear()
    response = await api.post(
        "/api/game/players",
        json={"nickname": "SATOSHI", "password": "pw", "email": "c@d.com"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Nickname taken"


@pytest.mark.parametrize("name", ["admin 1 !", "هوتن", "<b>"])
async def test_any_nickname_that_is_not_taken_is_fine(api, name):
    assert (await join(api, name))["nickname"] == name


async def test_login_is_remembered_for_a_year_only_when_asked(api):
    await join(api)
    body = {"nickname": "satoshi", "password": "pw"}
    short = await api.post("/api/game/login", json=body)
    long = await api.post("/api/game/login", json=body | {"remember": True})
    assert "max-age" not in short.headers["set-cookie"].lower()
    assert "max-age=31536000" in long.headers["set-cookie"].lower()


async def test_me_compares_the_wallet_with_holding_and_the_ai_team(api, session):
    session.add(MarketPrice(ts=NOW, symbol="BTCUSDT", price=PRICE, source="test"))
    await session.commit()
    await join(api)
    session.add(
        MarketPrice(
            ts=NOW + timedelta(minutes=5), symbol="BTCUSDT", price=88_000, source="test"
        )
    )
    await session.commit()

    me = (await api.get("/api/game/me")).json()

    assert me["return_pct"] == 0.0
    # Signed up at 80,000; BTC is now 88,000: holding would have made 10%.
    assert Decimal(me["hold_usd"]) == 110_000
    assert me["ai_return_pct"] == 0.0


async def test_three_nicknames_per_ip_a_day_and_failures_do_not_count(api):
    await join(api)
    api.cookies.clear()
    await api.post(
        "/api/game/players",
        json={"nickname": "satoshi", "password": "pw", "email": "a@b.com"},
    )
    for name in ("second", "third"):
        api.cookies.clear()
        await join(api, name)
    api.cookies.clear()
    response = await api.post(
        "/api/game/players",
        json={"nickname": "fourth", "password": "pw", "email": "a@b.com"},
    )
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

    # One prediction is enough to be ranked (frank has two).
    names = ["frank", "dana", "AI Trading Team", "erin"]
    assert [r["nickname"] for r in ever["rows"]] == names
    assert [r["return_pct"] for r in ever["rows"]] == [100.0, 10.0, 0.0, -5.0]
    assert [r["rank"] for r in ever["rows"]] == [1, 2, 3, 4]
    assert ever["rows"][2]["is_ai"] is True
    assert month["period"] == "month"
    # frank: 50,000 of it this month on 150,000 -> +33.33%.
    assert month["rows"][0]["return_pct"] == 33.33
    assert month["rows"][1] == {
        "rank": 2,
        "nickname": "dana",
        "return_pct": 0.92,
        "predictions": 3,
        "is_ai": False,
    }
    assert month["rows"][3]["return_pct"] == -5.0


async def test_full_game_day(api, session):
    """Join, predict, settle the next morning, and top the table."""
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


async def test_price_is_the_live_reference_price(api):
    response = await api.get("/api/game/price")
    assert Decimal(response.json()["price"]) == PRICE


async def test_trades_for_the_chart(api, session):
    session.add(
        PortfolioTrade(side="BUY", qty=Decimal("0.1"), price=PRICE, reason="test")
    )
    await session.commit()

    trades = (await api.get("/api/trading/trades")).json()

    assert [(t["side"], Decimal(t["price"])) for t in trades] == [("BUY", PRICE)]


async def test_live_price_is_kept_for_ten_seconds(monkeypatch):
    calls = []

    async def fetch(client):
        calls.append(1)
        return SimpleNamespace(price=Decimal(len(calls)))

    monkeypatch.setattr(game_api, "fetch_btc_price", fetch)
    monkeypatch.setattr(game_api, "PRICE_CACHE", [0.0, None])
    assert await game_api.live_price() == await game_api.live_price() == 1
    game_api.PRICE_CACHE[0] -= 11
    assert await game_api.live_price() == 2


async def test_admin_list_needs_the_admin_token(api, monkeypatch):
    await join(api, email="a@b.com")
    assert (await api.get("/api/admin/players")).status_code == 404
    monkeypatch.setattr(get_settings(), "admin_token", "secret")
    wrong = await api.get("/api/admin/players", headers={"X-Admin-Token": "nope"})
    assert wrong.status_code == 404

    rows = (
        await api.get("/api/admin/players", headers={"X-Admin-Token": "secret"})
    ).json()
    assert [(r["nickname"], r["password"], r["email"]) for r in rows] == [
        ("satoshi", "pw", "a@b.com")
    ]
