"""Prediction game endpoints: daily prediction, me, leaderboard and live price
(CLAUDE.md 4.2). Accounts are in accounts.py. No LLM is called here."""

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MarketPrice, Player, Prediction
from app.db.session import get_session
from app.game.leaderboard import Period, ai_row, leaderboard, pct
from app.game.players import require_player
from app.game.scoring import stake_usd, streak
from app.market.prices import PriceUnavailable, fetch_btc_price, make_client
from app.security.rate_limit import RateLimiter
from app.trading.portfolio import INITIAL_CASH
from app.trading.run import trading_day

router = APIRouter(prefix="/api/game")

PREDICTION_LIMITER = RateLimiter(5, timedelta(days=1))
HISTORY = 30
PRICE_TTL = 10
PRICE_CACHE: list = [0.0, None]


class NewPrediction(BaseModel):
    direction: Literal["up", "down"]
    stake_pct: Annotated[int, Field(ge=10, le=100, multiple_of=10)]


async def live_price() -> Decimal:
    """BTC price right now: a prediction's reference is the price when it is made.

    Kept for 10 seconds, so many visitors polling the page make few exchange calls.
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


def check_limit(limiter: RateLimiter, request: Request) -> None:
    """Count one action for the client IP, or answer 429."""
    if not limiter.allow(request.client.host):
        raise HTTPException(status_code=429, detail="Too many requests")


def prediction_out(p: Prediction) -> dict:
    """A prediction for the page."""
    return {
        "game_date": p.game_date,
        "direction": p.direction,
        "stake_pct": p.stake_pct,
        "stake_usd": p.stake_usd,
        "ref_price": p.ref_price,
        "result": p.result,
        "pnl_usd": p.pnl_usd,
        "created_at": p.created_at,
    }


async def me_out(session: AsyncSession, player: Player) -> dict:
    """Wallet, return, buy-and-hold since sign-up, the AI team's return to compare,
    streak, today's prediction and recent history, newest first."""
    rows = list(
        await session.scalars(
            select(Prediction)
            .where(Prediction.player_id == player.id)
            .order_by(Prediction.game_date.desc())
            .limit(HISTORY)
        )
    )
    now = datetime.now(UTC)
    today = trading_day(now)
    price = await session.scalar(
        select(MarketPrice.price).order_by(MarketPrice.ts.desc()).limit(1)
    )
    held = ai = None
    if price is not None:
        ai = (await ai_row(session, "all", now))["return_pct"]
        if player.signup_price:
            held = round(INITIAL_CASH * price / player.signup_price, 2)
    return {
        "nickname": player.nickname,
        "return_pct": pct(player.balance_usd - INITIAL_CASH, INITIAL_CASH),
        "hold_usd": held,
        "ai_return_pct": ai,
        "avatar": player.avatar is not None,
        "balance_usd": player.balance_usd,
        "streak": streak([p.result for p in rows if p.result]),
        "today": next((prediction_out(p) for p in rows if p.game_date == today), None),
        "predictions": [prediction_out(p) for p in rows],
    }


@router.post("/predictions", status_code=201)
async def predict(
    body: NewPrediction,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player, Depends(require_player)],
    price: Annotated[Decimal, Depends(live_price)],
) -> dict:
    """Today's one prediction at the current price."""
    day = trading_day(datetime.now(UTC))
    done = await session.scalar(
        select(Prediction.id)
        .where(Prediction.player_id == player.id)
        .where(Prediction.game_date == day)
    )
    if done:
        raise HTTPException(status_code=409, detail="One prediction per day")
    check_limit(PREDICTION_LIMITER, request)
    row = Prediction(
        player_id=player.id,
        game_date=day,
        direction=body.direction,
        stake_pct=body.stake_pct,
        stake_usd=stake_usd(player.balance_usd, body.stake_pct),
        ref_price=price,
    )
    session.add(row)
    await session.commit()
    return prediction_out(row)


@router.get("/me")
async def me(
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player, Depends(require_player)],
) -> dict:
    """The current player's wallet and predictions."""
    return await me_out(session, player)


@router.get("/leaderboard")
async def get_leaderboard(
    session: Annotated[AsyncSession, Depends(get_session)],
    period: Period = "month",
) -> dict:
    """Best percent return first; players appear after 3 settled predictions."""
    rows = await leaderboard(session, period, datetime.now(UTC))
    return {"period": period, "rows": rows}


@router.get("/price")
async def price_now(price: Annotated[Decimal, Depends(live_price)]) -> dict:
    """The BTC price a prediction made now would use as its reference."""
    return {"price": price}
