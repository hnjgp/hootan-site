"""Prediction game endpoints: nickname and wallet, daily prediction, me, recovery
and leaderboard (CLAUDE.md 4.2 and 4.3). No LLM is called here."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Player, Prediction
from app.db.session import get_session
from app.game.leaderboard import Period, leaderboard
from app.game.nickname import nickname_error
from app.game.players import (
    current_player,
    hash_token,
    new_recovery_token,
    require_player,
)
from app.game.scoring import stake_usd, streak
from app.market.prices import PriceUnavailable, fetch_btc_price, make_client
from app.security.cookie import set_player_cookie
from app.security.rate_limit import RateLimiter
from app.security.visitor import visitor_id
from app.trading.run import trading_day

router = APIRouter(prefix="/api/game")

# Only successful actions count, so a taken nickname does not use up a try.
NICKNAME_LIMITER = RateLimiter(3, timedelta(days=1))
PREDICTION_LIMITER = RateLimiter(5, timedelta(days=1))
HISTORY = 30


class NewPlayer(BaseModel):
    nickname: str


class NewPrediction(BaseModel):
    direction: Literal["up", "down"]
    stake_pct: Annotated[int, Field(ge=10, le=100, multiple_of=10)]


class Recovery(BaseModel):
    token: str


async def live_price() -> Decimal:
    """BTC price right now: a prediction's reference is the price when it is made."""
    try:
        async with make_client() as client:
            return (await fetch_btc_price(client)).price
    except PriceUnavailable:
        raise HTTPException(status_code=503, detail="Price unavailable") from None


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
    """Wallet, streak, today's prediction and recent history, newest first."""
    rows = list(
        await session.scalars(
            select(Prediction)
            .where(Prediction.player_id == player.id)
            .order_by(Prediction.game_date.desc())
            .limit(HISTORY)
        )
    )
    today = trading_day(datetime.now(UTC))
    return {
        "nickname": player.nickname,
        "balance_usd": player.balance_usd,
        "streak": streak([p.result for p in rows if p.result]),
        "today": next((prediction_out(p) for p in rows if p.game_date == today), None),
        "predictions": [prediction_out(p) for p in rows],
    }


@router.post("/players", status_code=201)
async def create_player(
    body: NewPlayer,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player | None, Depends(current_player)],
) -> dict:
    """Register a nickname, give a 100,000 USD wallet and set the signed cookie.

    The recovery token is shown once; only its hash is stored.
    """
    if player is not None:
        raise HTTPException(status_code=409, detail="Already playing")
    if error := nickname_error(body.nickname):
        raise HTTPException(status_code=422, detail=error)
    taken = await session.scalar(
        select(Player.id).where(func.lower(Player.nickname) == body.nickname.lower())
    )
    if taken:
        raise HTTPException(status_code=409, detail="Nickname taken")
    check_limit(NICKNAME_LIMITER, request)
    token, token_hash = new_recovery_token()
    settings = get_settings()
    player = Player(
        nickname=body.nickname,
        recovery_token_hash=token_hash,
        created_ip_hash=visitor_id(request, settings),
    )
    session.add(player)
    await session.commit()
    set_player_cookie(response, player.id, settings)
    return await me_out(session, player) | {"recovery_token": token}


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


@router.post("/recover")
async def recover(
    body: Recovery,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Bring a player to this device with the token from the recovery link."""
    player = await session.scalar(
        select(Player).where(Player.recovery_token_hash == hash_token(body.token))
    )
    if player is None:
        raise HTTPException(status_code=404, detail="Unknown recovery link")
    set_player_cookie(response, player.id, get_settings())
    return await me_out(session, player)


@router.get("/leaderboard")
async def get_leaderboard(
    session: Annotated[AsyncSession, Depends(get_session)],
    period: Period = "month",
) -> dict:
    """Best percent return first; players appear after 3 settled predictions."""
    rows = await leaderboard(session, period, datetime.now(UTC))
    return {"period": period, "rows": rows}
