"""Demo exchange endpoints: open and close positions, me, leaderboard and live price
(CLAUDE.md phase 10-b). Accounts are in accounts.py. No LLM is called here."""

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketPrice, Player, Position
from app.db.session import get_session
from app.exchange import book, calc
from app.game.leaderboard import Period, leaderboard, pct
from app.game.players import require_player
from app.market.prices import PriceUnavailable, fetch_btc_price, make_client
from app.security.rate_limit import RateLimiter

router = APIRouter(prefix="/api/game")

ORDER_LIMITER = RateLimiter(200, timedelta(days=1))
MAX_OPEN = 20
HISTORY = 20
PRICE_TTL = 5
PRICE_CACHE: list = [0.0, None]


class NewPosition(BaseModel):
    side: Literal["long", "short"]
    margin_usd: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2)]
    leverage: Annotated[int, Field(ge=1, le=100)]
    tp_price: (
        Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2)] | None
    ) = None
    sl_price: (
        Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=2)] | None
    ) = None


async def live_price() -> Decimal:
    """BTC price right now: orders fill and equity is valued at it.

    Kept for 5 seconds, so many visitors polling the page make few exchange calls.
    """
    fetched_at, price = PRICE_CACHE
    if price is not None and time.monotonic() - fetched_at < PRICE_TTL:
        return price
    try:
        async with make_client() as client:
            price = (await fetch_btc_price(client)).price
    except PriceUnavailable:
        raise HTTPException(status_code=503, detail="Price unavailable") from None
    PRICE_CACHE[:] = [time.monotonic(), price]
    return price


async def shown_price(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Decimal:
    """Price for showing an account: live, or the last stored one when the exchanges
    are down, so logging in never fails for it. Orders always need the live price."""
    try:
        return await live_price()
    except HTTPException:
        price = await session.scalar(
            select(MarketPrice.price).order_by(MarketPrice.ts.desc()).limit(1)
        )
        if price is None:
            raise
        return price


def check_limit(limiter: RateLimiter, request: Request) -> None:
    """Count one action for the client IP, or answer 429."""
    if not limiter.allow(request.client.host):
        raise HTTPException(status_code=429, detail="Too many requests")


async def me_out(session: AsyncSession, player: Player, price: Decimal) -> dict:
    """Cash, equity and return at `price`, buy-and-hold since sign-up, the AI team's
    return to compare, open positions and the latest closed ones."""
    mine = await book.load_book(session, player.id)
    team = await book.load_book(session, None)
    equity = mine.equity(price)
    closed = await session.scalars(
        select(Position)
        .where(Position.player_id == player.id, Position.closed_at.is_not(None))
        .order_by(Position.closed_at.desc())
        .limit(HISTORY)
    )
    held = None
    if player.signup_price:
        held = calc.cents(calc.START_USD * price / player.signup_price)
    return {
        "nickname": player.nickname,
        "avatar": player.avatar is not None,
        "price": price,
        "cash_usd": calc.cents(mine.cash),
        "equity_usd": equity,
        "return_pct": pct(equity - calc.START_USD, calc.START_USD),
        "hold_usd": held,
        "ai_return_pct": pct(team.equity(price) - calc.START_USD, calc.START_USD),
        "open": [book.position_out(p, price) for p in mine.open],
        "closed": [book.position_out(p, price) for p in closed],
    }


@router.get("/me")
async def me(
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player, Depends(require_player)],
    price: Annotated[Decimal, Depends(shown_price)],
) -> dict:
    """The current player's account at the current price."""
    return await me_out(session, player, price)


@router.post("/positions", status_code=201)
async def open_order(
    body: NewPosition,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player, Depends(require_player)],
    price: Annotated[Decimal, Depends(live_price)],
) -> dict:
    """Open a position at the live price; 422 with a short code when it is refused."""
    check_limit(ORDER_LIMITER, request)
    if len((await book.load_book(session, player.id)).open) >= MAX_OPEN:
        raise HTTPException(status_code=422, detail="open")
    try:
        await book.open_position(
            session,
            player.id,
            body.side,
            body.margin_usd,
            body.leverage,
            price,
            body.tp_price,
            body.sl_price,
        )
    except book.OrderError as e:
        await session.rollback()
        raise HTTPException(status_code=422, detail=str(e)) from None
    await session.commit()
    return await me_out(session, player, price)


@router.post("/positions/{position_id}/close")
async def close_order(
    position_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player, Depends(require_player)],
    price: Annotated[Decimal, Depends(live_price)],
) -> dict:
    """Close one of the player's open positions at the live price."""
    closed = await book.close_position(session, player.id, position_id, price, "manual")
    if closed is None:
        raise HTTPException(status_code=404, detail="No such open position")
    await session.commit()
    return await me_out(session, player, price)


@router.get("/leaderboard")
async def get_leaderboard(
    session: Annotated[AsyncSession, Depends(get_session)],
    price: Annotated[Decimal, Depends(shown_price)],
    period: Period = "month",
) -> dict:
    """Best percent return first; a player appears after opening a position."""
    rows = await leaderboard(session, period, price, datetime.now(UTC))
    return {"period": period, "rows": rows}


@router.get("/price")
async def price_now(price: Annotated[Decimal, Depends(live_price)]) -> dict:
    """The BTC price an order placed now would fill at."""
    return {"price": price}
