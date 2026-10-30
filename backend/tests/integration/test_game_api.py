import itertools
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import httpx2
import pytest
from sqlalchemy import select

from app.config import get_settings
from app.db.models import (
    Player,
)
from app.db.session import get_session
from app.game import api as game_api
from app.game.accounts import JPEG, LOGIN_LIMITER, SIGNUP_LIMITER
from app.game.api import live_price, shown_price
from app.main import app
from app.security.cookie import sign
from app.trading.run import trading_day

NOW = datetime.now(UTC)
TODAY = trading_day(NOW)
YESTERDAY = TODAY - timedelta(days=1)
PRICE = Decimal(80_000)
EMAILS = itertools.count()


@pytest.fixture
async def api(session):
    """HTTPS client (the cookie is Secure) with the test session and a fixed live price."""
    for limiter in (SIGNUP_LIMITER, LOGIN_LIMITER):
        limiter.hits.clear()
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[live_price] = lambda: PRICE
    app.dependency_overrides[shown_price] = lambda: PRICE
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="https://test") as c:
        yield c
    app.dependency_overrides.clear()


async def join(api, nickname: str = "satoshi", **extra) -> dict:
    body = {"nickname": nickname, "password": "pw", "email": f"p{next(EMAILS)}@b.com"}
    body |= extra
    response = await api.post("/api/game/players", json=body)
    assert response.status_code == 201
    return response.json()


def player_cookie(response) -> str:
    """The Set-Cookie header of the log-in cookie, lowercased."""
    headers = response.headers.get_list("set-cookie")
    return next(h for h in headers if h.startswith("player=")).lower()


async def test_signing_up_stores_the_account_and_logs_in(api, session):
    body = await join(api, email="a@b.com", phone="+98 912 000 0000")

    assert body["nickname"] == "satoshi"
    assert Decimal(body["cash_usd"]) == Decimal(body["equity_usd"]) == 10_000
    assert body["open"] == body["closed"] == []
    assert body["avatar"] is False
    assert "player" in api.cookies
    player = await session.scalar(select(Player))
    assert player.signup_price == PRICE
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
    assert (await api.get("/api/game/me")).json() is None

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
    assert "max-age" not in player_cookie(short)
    assert "max-age=31536000" in player_cookie(long)


async def test_me_compares_the_account_with_holding_and_the_ai_team(api):
    await join(api)
    app.dependency_overrides[shown_price] = lambda: Decimal(88_000)

    me = (await api.get("/api/game/me")).json()

    assert me["return_pct"] == 0.0
    # Signed up at 80,000; BTC is now 88,000: holding would have made 10%.
    assert Decimal(me["hold_usd"]) == 11_000
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
        json={"nickname": "fourth", "password": "pw", "email": "fourth@b.com"},
    )
    assert response.status_code == 429


async def test_trading_needs_a_login(api):
    response = await api.post(
        "/api/game/positions",
        json={"side": "long", "margin_usd": "100", "leverage": 1},
    )
    assert response.status_code == 401


async def test_forged_cookie_is_not_a_player(api, session):
    await join(api)
    player = await session.scalar(select(Player))
    api.cookies.clear()
    api.cookies.set("player", f"{player.id}.forged")
    assert (await api.get("/api/game/me")).json() is None
    api.cookies.set("player", sign(player.id, get_settings()))
    assert (await api.get("/api/game/me")).status_code == 200


async def test_price_is_the_live_order_price(api):
    response = await api.get("/api/game/price")
    assert Decimal(response.json()["price"]) == PRICE


async def test_live_price_is_kept_for_five_seconds(monkeypatch):
    calls = []

    async def fetch(client):
        calls.append(1)
        return SimpleNamespace(price=Decimal(len(calls)))

    monkeypatch.setattr(game_api, "fetch_btc_price", fetch)
    monkeypatch.setattr(game_api, "PRICE_CACHE", [0.0, None])
    assert await game_api.live_price() == await game_api.live_price() == 1
    game_api.PRICE_CACHE[0] -= 6
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


async def test_a_remembered_account_logs_back_in_after_logout_without_a_password(api):
    await join(api)
    body = {"nickname": "satoshi", "password": "pw", "remember": True}
    await api.post("/api/game/login", json=body)
    await api.post("/api/game/logout")
    assert (await api.get("/api/game/me")).json() is None

    offered = await api.get("/api/game/remembered")
    back = await api.post("/api/game/login/remembered")

    assert offered.json() == {"nickname": "satoshi"}
    assert back.status_code == 200
    assert (await api.get("/api/game/me")).json()["nickname"] == "satoshi"


async def test_logging_in_without_remember_forgets_the_account(api):
    await join(api)
    body = {"nickname": "satoshi", "password": "pw"}
    await api.post("/api/game/login", json=body | {"remember": True})
    await api.post("/api/game/login", json=body)
    await api.post("/api/game/logout")

    assert (await api.get("/api/game/remembered")).status_code == 404
    assert (await api.post("/api/game/login/remembered")).status_code == 404


async def test_forgetting_stops_the_offer(api):
    await join(api)
    await api.post(
        "/api/game/login",
        json={"nickname": "satoshi", "password": "pw", "remember": True},
    )
    await api.post("/api/game/logout")

    assert (await api.delete("/api/game/remembered")).status_code == 204
    assert (await api.get("/api/game/remembered")).status_code == 404


async def test_a_forged_remember_cookie_is_ignored(api, session):
    await join(api)
    player = await session.scalar(select(Player))
    api.cookies.clear()
    api.cookies.set("remembered", f"{player.id}.forged")

    assert (await api.post("/api/game/login/remembered")).status_code == 404


async def test_nobody_can_sign_up_with_the_admin_nickname(api):
    body = {"nickname": "hootan", "password": "pw", "email": "x@b.com"}
    response = await api.post("/api/game/players", json=body)
    assert response.status_code == 409


async def test_the_admin_account_opens_the_admin_endpoints(api, session, monkeypatch):
    await join(api)
    assert (await api.get("/api/admin/overview")).status_code == 404
    assert (await api.get("/api/game/me")).json()["admin"] is False

    monkeypatch.setattr(get_settings(), "admin_nickname", "Satoshi")
    assert (await api.get("/api/game/me")).json()["admin"] is True
    overview = (await api.get("/api/admin/overview")).json()
    assert overview["counts"]["players"]["today"] == 1
    assert "today" in overview["costs"]
    for path in ("players", "leads", "jobfits", "chats"):
        assert (await api.get(f"/api/admin/{path}")).status_code == 200
