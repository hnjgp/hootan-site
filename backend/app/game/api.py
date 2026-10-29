"""Prediction game endpoints: daily prediction, me, leaderboard, live price and
stats (CLAUDE.md 4.2). Accounts are in accounts.py. No LLM is called here."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Player, Prediction
from app.db.session import get_session
from app.game.leaderboard import Period, ai_row, leaderboard, player_rows
from app.game.players import require_player
from app.game.scoring import stake_usd, streak
from app.game.stats import players_ahead, recent_trades, team_accuracy
from app.market.prices import PriceUnavailable, fetch_btc_price, make_client
from app.security.rate_limit import RateLimiter
from app.trading.run import trading_day

router = APIRouter(prefix="/api/game")

PREDICTION_LIMITER = RateLimiter(5, timedelta(days=1))
HISTORY = 30


class NewPrediction(BaseModel):
    direction: Literal["up", "down"]
    stake_pct: Annotated[int, Field(ge=10, le=100, multiple_of=10)]


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


@router.get("/stats")
async def get_stats(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Team accuracy this season, players ahead of the team this month, team trades."""
    now = datetime.now(UTC)
    right, decided = await team_accuracy(session, now)
    rows = await player_rows(session, "month", now)
    ahead, players = players_ahead(rows + [await ai_row(session, "month", now)])
    return {
        "accuracy_pct": round(right / decided * 100) if decided else None,
        "decided": decided,
        "ahead_pct": round(ahead / players * 100) if players else None,
        "players": players,
        "trades": await recent_trades(session),
    }
