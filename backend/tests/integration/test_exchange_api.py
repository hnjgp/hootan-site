import itertools
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import httpx2
import pytest
from sqlalchemy import select

from app.db.models import EquitySnapshot, Player, Position
from app.db.session import get_session
from app.exchange import book
from app.game.accounts import SIGNUP_LIMITER
from app.game.api import ORDER_LIMITER, live_price, shown_price
from app.game.leaderboard import AI_NAME
from app.game.season import season_day
from app.main import app

PRICE = Decimal(80_000)
NOW = datetime.now(UTC)
EMAILS = itertools.count()


@pytest.fixture
async def api(session):
    """HTTPS client with the test session; `api.price` sets the live price."""
    for limiter in (SIGNUP_LIMITER, ORDER_LIMITER):
        limiter.hits.clear()
    price = [PRICE]
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[live_price] = lambda: price[0]
    app.dependency_overrides[shown_price] = lambda: price[0]
    transport = httpx2.ASGITransport(app=app)
    async with httpx2.AsyncClient(transport=transport, base_url="https://test") as c:
        c.price = lambda p: price.__setitem__(0, Decimal(p))
        yield c
    app.dependency_overrides.clear()


async def join(api, nickname="satoshi"):
    body = {"nickname": nickname, "password": "pw", "email": f"p{next(EMAILS)}@b.com"}
    response = await api.post("/api/game/players", json=body)
    assert response.status_code == 201
    return response.json()


async def order(api, **body):
    defaults = {"side": "long", "margin_usd": "1000", "leverage": 10}
    return await api.post("/api/game/positions", json=defaults | body)


async def test_opening_takes_margin_and_fee_from_cash(api):
    await join(api)

    response = await order(api, tp_price="85000", sl_price="78000")

    assert response.status_code == 201
    me = response.json()
    assert Decimal(me["cash_usd"]) == Decimal("8995.00")
    assert Decimal(me["equity_usd"]) == Decimal("9995.00")
    [p] = me["open"]
    assert (p["side"], p["leverage"], Decimal(p["qty"])) == (
        "long",
        10,
        Decimal("0.125"),
    )
    assert Decimal(p["liq_price"]) == 72_000
    assert Decimal(p["fee_usd"]) == 5


async def test_equity_floats_with_the_price(api):
    await join(api)
    await order(api)
    api.price(82_000)

    me = (await api.get("/api/game/me")).json()

    assert Decimal(me["open"][0]["pnl_usd"]) == 250
    assert Decimal(me["equity_usd"]) == Decimal("10245.00")
    assert me["return_pct"] == 2.45


async def test_closing_by_hand_pays_profit_minus_the_closing_fee(api):
    await join(api)
    opened = (await order(api, side="short")).json()["open"][0]
    api.price(78_000)

    response = await api.post(f"/api/game/positions/{opened['id']}/close")

    me = response.json()
    assert me["open"] == []
    [p] = me["closed"]
    assert p["close_reason"] == "manual"
    # +250 profit, 5 to open, 5 to close.
    assert Decimal(p["pnl_usd"]) == 240
    assert Decimal(me["cash_usd"]) == Decimal(10_240)
    again = await api.post(f"/api/game/positions/{opened['id']}/close")
    assert again.status_code == 404


async def test_a_player_cannot_close_someone_elses_position(api):
    await join(api)
    opened = (await order(api)).json()["open"][0]
    api.cookies.clear()
    await join(api, "mallory")

    response = await api.post(f"/api/game/positions/{opened['id']}/close")

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ({"margin_usd": "9999"}, "cash"),
        ({"margin_usd": "0.5"}, "margin"),
        ({"tp_price": "79000"}, "tp"),
        ({"sl_price": "81000"}, "sl"),
        ({"sl_price": "71000"}, "sl"),
        ({"side": "short", "tp_price": "81000"}, "tp"),
    ],
)
async def test_orders_the_exchange_refuses(api, body, code):
    await join(api)

    response = await order(api, **body)

    assert response.status_code == 422
    assert response.json()["detail"] == code
    assert (await api.get("/api/game/me")).json()["open"] == []


@pytest.mark.parametrize("body", [{"leverage": 0}, {"leverage": 101}, {"side": "up"}])
async def test_out_of_range_orders_are_invalid(api, body):
    await join(api)
    assert (await order(api, **body)).status_code == 422


async def test_all_cash_at_once_fits_with_its_fee(api):
    await join(api)

    response = await order(api, margin_usd="9950.24")

    assert response.status_code == 201
    assert Decimal(response.json()["cash_usd"]) >= 0


async def test_triggers_close_take_profit_stop_loss_and_liquidation(api, session):
    await join(api)
    await order(api, tp_price="84000")
    await order(api, side="short", sl_price="82000")
    await order(api, leverage=100, margin_usd="100")

    hit = await book.check_triggers(session, Decimal(84_000))

    assert {(p.side, p.close_reason) for p in hit} == {("long", "tp"), ("short", "sl")}
    me = (await api.get("/api/game/me")).json()
    by_reason = {p["close_reason"]: Decimal(p["pnl_usd"]) for p in me["closed"]}
    # Long 0.125 BTC from 80,000 to 84,000: +500, minus 5 + 5 in fees.
    assert by_reason["tp"] == 490
    # Short 0.125 BTC: -500 and fees.
    assert by_reason["sl"] == -510


async def test_liquidation_loses_the_margin_and_nothing_more(api, session):
    await join(api)
    await order(api, leverage=100, margin_usd="100")

    [p] = await book.check_triggers(session, Decimal(70_000))

    assert p.close_reason == "liq"
    # The 100 USD margin and the 5 USD opening fee; no closing fee.
    assert p.pnl_usd == -105
    me = (await api.get("/api/game/me")).json()
    assert Decimal(me["cash_usd"]) == 9_895


async def test_nothing_fires_between_the_levels(api, session):
    await join(api)
    await order(api, tp_price="84000", sl_price="78000")

    assert await book.check_triggers(session, Decimal(81_000)) == []


async def test_twenty_open_positions_at_most(api):
    await join(api)
    for _ in range(20):
        assert (await order(api, margin_usd="10", leverage=1)).status_code == 201

    response = await order(api, margin_usd="10", leverage=1)

    assert response.json()["detail"] == "open"


async def test_the_team_has_its_own_book(session):
    await book.open_position(session, None, "short", Decimal(500), 2, PRICE)
    await session.commit()

    team = await book.load_book(session, None)

    assert team.cash == Decimal("9499.50")
    assert len(team.open) == 1
    assert team.equity(Decimal(76_000)) == Decimal("10049.50")


async def test_snapshots_once_per_owner_and_day(api, session):
    await join(api)
    await order(api)
    day = NOW.date()

    await book.take_snapshots(session, Decimal(81_000), day)
    await book.take_snapshots(session, Decimal(90_000), day)

    rows = list(await session.scalars(select(EquitySnapshot)))
    assert len(rows) == 2
    equity = {r.player_id is None: r.equity_usd for r in rows}
    assert equity == {True: 10_000, False: Decimal("10120.00")}


async def test_leaderboard_ranks_return_on_equity_with_the_ai_team(api, session):
    await join(api)
    await order(api)
    api.cookies.clear()
    await join(api, "bear")
    await order(api, side="short")
    api.cookies.clear()
    await join(api, "watcher")
    api.price(84_000)

    rows = (await api.get("/api/game/leaderboard?period=all")).json()["rows"]

    assert [(r["rank"], r["nickname"]) for r in rows] == [
        (1, "satoshi"),
        (2, AI_NAME),
        (3, "bear"),
    ]
    assert rows[0]["return_pct"] == 4.95
    assert rows[1]["is_ai"] is True


async def test_the_month_counts_from_the_first_snapshot_of_the_season(api, session):
    await join(api)
    await order(api, margin_usd="2000", leverage=1)
    player = await session.scalar(select(Player))
    session.add(
        EquitySnapshot(
            day=season_day(NOW),
            player_id=player.id,
            equity_usd=Decimal(9_000),
            price=PRICE,
        )
    )
    await session.commit()

    rows = (await api.get("/api/game/leaderboard?period=month")).json()["rows"]

    mine = next(r for r in rows if r["nickname"] == "satoshi")
    assert mine["return_pct"] == round((9999 - 9000) / 9000 * 100, 2)


async def test_team_meeting_positions_show_on_the_chart(api, session):
    position = await book.open_position(session, None, "long", Decimal(500), 2, PRICE)
    book.settle(position, Decimal(81_000), "team", NOW + timedelta(hours=1))
    await session.commit()

    marks = (await api.get("/api/trading/trades")).json()

    assert [(m["side"], Decimal(m["price"])) for m in marks] == [
        ("long", PRICE),
        ("close", Decimal(81_000)),
    ]
    assert await session.scalar(select(Position.pnl_usd)) == Decimal("11.50")
