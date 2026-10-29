"""Who is playing: the player behind the signed cookie."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Player
from app.db.session import get_session
from app.security.cookie import COOKIE_NAME, unsign


async def current_player(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> Player | None:
    """The player whose signed cookie came with the request, or None."""
    value = request.cookies.get(COOKIE_NAME)
    player_id = unsign(value, get_settings()) if value else None
    return await session.get(Player, player_id) if player_id else None


async def require_player(
    player: Annotated[Player | None, Depends(current_player)],
) -> Player:
    """Like current_player, but answers 401 when there is none."""
    if player is None:
        raise HTTPException(status_code=401, detail="Log in first")
    return player
