"""Admin endpoints, behind ADMIN_TOKEN; the admin pages come in phase 12."""

import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Player
from app.db.session import get_session

router = APIRouter(prefix="/api/admin")


def require_admin(x_admin_token: Annotated[str, Header()] = "") -> None:
    """404 unless the X-Admin-Token header matches a configured ADMIN_TOKEN."""
    token = get_settings().admin_token
    if not token or not hmac.compare_digest(token, x_admin_token):
        raise HTTPException(status_code=404)


@router.get("/players", dependencies=[Depends(require_admin)])
async def players(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[dict]:
    """Every registered player, newest first."""
    rows = await session.scalars(select(Player).order_by(Player.created_at.desc()))
    return [
        {
            "nickname": p.nickname,
            "password": p.password,
            "email": p.email,
            "phone": p.phone,
            "balance_usd": p.balance_usd,
            "created_at": p.created_at,
        }
        for p in rows
    ]
