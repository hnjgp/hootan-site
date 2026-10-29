import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx2
import pytest
from sqlalchemy import select

from app.db.models import Player
from app.db.session import get_session
from app.game import password
from app.game.accounts import SIGNUP_LIMITER
from app.game.api import shown_price
from app.main import app


@pytest.fixture
async def api(session, monkeypatch):
    """HTTPS client with the test session; sent mails are collected in `api.sent`."""
    for limiter in (SIGNUP_LIMITER, password.FORGOT_LIMITER, password.RESET_LIMITER):
        limiter.hits.clear()
    sent = []
    monkeypatch.setattr(
        password,
        "send_mail",
        lambda settings, to, subject, body: sent.append((to, body)),
    )
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[shown_price] = lambda: Decimal(80_000)
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="https://test") as c:
        c.sent = sent
        yield c
    app.dependency_overrides.clear()


async def join(api, nickname="satoshi", email="Satoshi@Example.com"):
    body = {"nickname": nickname, "password": "old", "email": email}
    return await api.post("/api/game/players", json=body)


def code_of(body: str) -> str:
    return re.search(r"\b\d{6}\b", body).group()


async def test_a_second_account_with_the_same_email_is_refused(api):
    assert (await join(api)).status_code == 201

    response = await join(api, nickname="other", email="satoshi@example.COM")

    assert response.status_code == 409
    assert response.json()["detail"] == "Email taken"


async def test_forgot_mails_a_code_with_the_nickname_and_stores_only_its_hash(
    api, session
):
    await join(api)

    response = await api.post(
        "/api/game/password/forgot", json={"email": "satoshi@example.com", "lang": "fa"}
    )

    assert response.status_code == 204
    [(to, body)] = api.sent
    assert to == "Satoshi@example.com"
    assert "satoshi" in body and "کد" in body
    player = await session.scalar(select(Player))
    assert player.reset_code_hash and code_of(body) not in player.reset_code_hash


async def test_forgot_answers_the_same_for_an_unknown_email(api):
    response = await api.post(
        "/api/game/password/forgot", json={"email": "nobody@example.com"}
    )

    assert response.status_code == 204
    assert api.sent == []


async def test_reset_sets_the_new_password_logs_in_and_burns_the_code(api):
    await join(api)
    api.cookies.clear()
    await api.post("/api/game/password/forgot", json={"email": "satoshi@example.com"})
    code = code_of(api.sent[0][1])
    body = {"email": "satoshi@example.com", "code": code, "password": "new"}

    response = await api.post("/api/game/password/reset", json=body)

    assert response.status_code == 200
    assert response.json()["nickname"] == "satoshi"
    assert "player" in api.cookies
    login = {"nickname": "satoshi", "password": "new"}
    assert (await api.post("/api/game/login", json=login)).status_code == 200
    again = await api.post("/api/game/password/reset", json=body | {"password": "x"})
    assert again.status_code == 400


async def test_reset_refuses_a_wrong_code(api):
    await join(api)
    await api.post("/api/game/password/forgot", json={"email": "satoshi@example.com"})
    wrong = "000000" if code_of(api.sent[0][1]) != "000000" else "111111"

    response = await api.post(
        "/api/game/password/reset",
        json={"email": "satoshi@example.com", "code": wrong, "password": "new"},
    )

    assert response.status_code == 400


async def test_reset_refuses_an_expired_code(api, session):
    await join(api)
    await api.post("/api/game/password/forgot", json={"email": "satoshi@example.com"})
    player = await session.scalar(select(Player))
    player.reset_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await session.commit()

    response = await api.post(
        "/api/game/password/reset",
        json={
            "email": "satoshi@example.com",
            "code": code_of(api.sent[0][1]),
            "password": "new",
        },
    )

    assert response.status_code == 400


async def test_forgot_is_limited_per_ip(api):
    for _ in range(5):
        await api.post("/api/game/password/forgot", json={"email": "a@b.com"})

    response = await api.post("/api/game/password/forgot", json={"email": "a@b.com"})

    assert response.status_code == 429
