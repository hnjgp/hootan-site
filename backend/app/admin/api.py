"""Admin endpoints: for Hootan's own account, or with the ADMIN_TOKEN header."""

import hmac
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import (
    ChatLog,
    JobFitRequest,
    Lead,
    LLMUsage,
    MarketPrice,
    Player,
    Position,
    TradingSession,
)
from app.db.session import get_session
from app.game.players import current_player, is_admin
from app.llm.budget import day_and_month_start

LATEST = 20


def require_admin(
    player: Annotated[Player | None, Depends(current_player)],
    x_admin_token: Annotated[str, Header()] = "",
) -> None:
    """404 unless the admin is logged in or X-Admin-Token matches ADMIN_TOKEN."""
    if player is not None and is_admin(player):
        return
    token = get_settings().admin_token
    if not token or not hmac.compare_digest(token, x_admin_token):
        raise HTTPException(status_code=404)


router = APIRouter(prefix="/api/admin", dependencies=[Depends(require_admin)])
Session = Annotated[AsyncSession, Depends(get_session)]


async def costs_since(session: AsyncSession, start: datetime) -> dict[str, float]:
    """LLM cost in USD per feature since `start`."""
    rows = await session.execute(
        select(LLMUsage.feature, func.sum(LLMUsage.cost_usd))
        .where(LLMUsage.ts >= start)
        .group_by(LLMUsage.feature)
    )
    return {feature: float(total) for feature, total in rows}


async def count_since(session: AsyncSession, column, start: datetime) -> int:
    """Rows of column's table created since `start`."""
    return await session.scalar(select(func.count()).where(column >= start))


@router.get("/overview")
async def overview(session: Session) -> dict:
    """Costs, caps, activity counts, the last trading meeting and the last price.

    Days and months follow the Asia/Tehran calendar, like the budget guard.
    """
    settings = get_settings()
    day, month = day_and_month_start(datetime.now(UTC))
    counts = {}
    for name, column in (
        ("chats", ChatLog.created_at),
        ("jobfits", JobFitRequest.created_at),
        ("positions", Position.opened_at),
        ("players", Player.created_at),
        ("leads", Lead.created_at),
    ):
        counts[name] = {
            "today": await count_since(session, column, day),
            "month": await count_since(session, column, month),
        }
    meeting = await session.scalar(
        select(TradingSession).order_by(TradingSession.session_date.desc()).limit(1)
    )
    return {
        "ai_enabled": settings.ai_enabled,
        "caps": {
            "monthly": float(settings.budget_monthly_usd),
            "trading_daily": float(settings.budget_trading_daily_usd),
            "public_daily": float(settings.budget_public_daily_usd),
        },
        "costs": {
            "today": await costs_since(session, day),
            "month": await costs_since(session, month),
        },
        "counts": counts,
        "meeting": meeting
        and {
            "date": meeting.session_date,
            "status": meeting.status,
            "decision": meeting.decision,
            "cost_usd": float(meeting.cost_usd),
            "finished_at": meeting.finished_at,
        },
        "last_price_at": await session.scalar(select(func.max(MarketPrice.ts))),
    }


@router.get("/players")
async def players(session: Session) -> list[dict]:
    """Every registered player, newest first."""
    rows = await session.scalars(select(Player).order_by(Player.created_at.desc()))
    return [
        {
            "nickname": p.nickname,
            "password": p.password,
            "email": p.email,
            "phone": p.phone,
            "created_at": p.created_at,
        }
        for p in rows
    ]


@router.get("/leads")
async def leads(session: Session) -> list[dict]:
    """Emails visitors left for Hootan, newest first."""
    rows = await session.scalars(select(Lead).order_by(Lead.created_at.desc()))
    return [
        {"email": r.email, "context": r.context, "created_at": r.created_at}
        for r in rows
    ]


@router.get("/jobfits")
async def jobfits(session: Session) -> list[dict]:
    """The latest job-fit checks with their score, the ad, and who asked if logged in."""
    rows = await session.execute(
        select(JobFitRequest, Player.nickname, Player.email)
        .outerjoin(Player, JobFitRequest.player_id == Player.id)
        .order_by(JobFitRequest.created_at.desc())
        .limit(LATEST)
    )
    return [
        {
            "nickname": nickname,
            "email": email,
            "score": r.score,
            "lang": r.lang,
            "jd_text": r.jd_text,
            "result": r.result,
            "created_at": r.created_at,
        }
        for r, nickname, email in rows
    ]


@router.get("/chats")
async def chats(session: Session) -> list[dict]:
    """The latest twin questions and answers, and who asked if logged in."""
    rows = await session.execute(
        select(ChatLog, Player.nickname, Player.email)
        .outerjoin(Player, ChatLog.player_id == Player.id)
        .order_by(ChatLog.created_at.desc())
        .limit(LATEST)
    )
    return [
        {
            "nickname": nickname,
            "email": email,
            "question": r.question,
            "answer": r.answer,
            "created_at": r.created_at,
        }
        for r, nickname, email in rows
    ]
