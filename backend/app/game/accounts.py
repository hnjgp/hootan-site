"""Player accounts: sign up, log in, log out and a profile photo.

Any nickname that is not taken (1 to 20 characters, the column size), any password,
a required email and an optional phone. The signed cookie says who is logged in.
"""

from datetime import timedelta
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field, StringConstraints
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Player
from app.db.session import get_session
from app.game.api import check_limit, me_out, shown_price
from app.game.players import require_player
from app.security.cookie import (
    COOKIE_NAME,
    FLAGS,
    REMEMBER_NAME,
    set_player_cookie,
    unsign,
)
from app.security.rate_limit import RateLimiter
from app.security.visitor import visitor_id

router = APIRouter(prefix="/api/game")

# Only successful sign-ups count, so a taken nickname does not use up a try.
SIGNUP_LIMITER = RateLimiter(3, timedelta(days=1))
# Every login try counts, so passwords cannot be guessed quickly.
LOGIN_LIMITER = RateLimiter(20, timedelta(hours=1))
AVATAR_MAX = 100_000
JPEG = b"\xff\xd8\xff"

Nickname = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)
]
Password = Annotated[str, Field(min_length=1, max_length=128)]


class LogIn(BaseModel):
    nickname: Nickname
    password: Password
    remember: bool = False


class SignUp(LogIn):
    email: EmailStr
    phone: Annotated[str, Field(pattern=r"^\+?[\d\s-]{5,20}$")] | None = None


async def by_nickname(session: AsyncSession, nickname: str) -> Player | None:
    """The player with this nickname, ignoring case."""
    return await session.scalar(
        select(Player).where(func.lower(Player.nickname) == nickname.lower())
    )


@router.post("/players", status_code=201)
async def sign_up(
    body: SignUp,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    price: Annotated[Decimal, Depends(shown_price)],
) -> dict:
    """Create an account with 10,000 USD of cash and log it in."""
    settings = get_settings()
    reserved = body.nickname.lower() == settings.admin_nickname.lower()
    if reserved or await by_nickname(session, body.nickname):
        raise HTTPException(status_code=409, detail="Nickname taken")
    taken = await session.scalar(
        select(Player.id).where(func.lower(Player.email) == body.email.lower())
    )
    if taken:
        raise HTTPException(status_code=409, detail="Email taken")
    check_limit(SIGNUP_LIMITER, request)
    player = Player(
        nickname=body.nickname,
        password=body.password,
        email=body.email,
        phone=body.phone,
        signup_price=price,
        created_ip_hash=visitor_id(request, settings),
    )
    session.add(player)
    await session.commit()
    set_player_cookie(response, player.id, settings, body.remember)
    return await me_out(session, player, price)


@router.post("/login")
async def log_in(
    body: LogIn,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    price: Annotated[Decimal, Depends(shown_price)],
) -> dict:
    """Log in with nickname and password; 401 when either is wrong.

    Remembered for a year when `remember` is set, else until the browser closes.
    """
    check_limit(LOGIN_LIMITER, request)
    player = await by_nickname(session, body.nickname)
    if player is None or player.password != body.password:
        raise HTTPException(status_code=401, detail="Wrong nickname or password")
    set_player_cookie(response, player.id, get_settings(), body.remember)
    return await me_out(session, player, price)


@router.post("/logout", status_code=204)
async def log_out(response: Response) -> None:
    """Forget who is logged in on this browser; a remembered account stays offered."""
    response.delete_cookie(COOKIE_NAME, **FLAGS)


async def remembered_player(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> Player:
    """The player this browser remembers, or 404."""
    value = request.cookies.get(REMEMBER_NAME)
    player_id = unsign(value, get_settings()) if value else None
    player = await session.get(Player, player_id) if player_id else None
    if player is None:
        raise HTTPException(status_code=404, detail="Nothing remembered")
    return player


@router.get("/remembered")
async def remembered(
    player: Annotated[Player, Depends(remembered_player)],
) -> dict:
    """The remembered nickname, for the log-in form to fill in."""
    return {"nickname": player.nickname}


@router.post("/login/remembered")
async def log_in_remembered(
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player, Depends(remembered_player)],
    price: Annotated[Decimal, Depends(shown_price)],
) -> dict:
    """Log the remembered player back in without a password, remembered again."""
    check_limit(LOGIN_LIMITER, request)
    set_player_cookie(response, player.id, get_settings(), remember=True)
    return await me_out(session, player, price)


@router.delete("/remembered", status_code=204)
async def forget(response: Response) -> None:
    """Stop offering the remembered account on this browser."""
    response.delete_cookie(REMEMBER_NAME, **FLAGS)


@router.put("/me/avatar", status_code=204)
async def set_avatar(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    player: Annotated[Player, Depends(require_player)],
) -> None:
    """Store the profile photo: a JPEG body the browser already shrank, at most 100 KB."""
    image = await request.body()
    if len(image) > AVATAR_MAX or not image.startswith(JPEG):
        raise HTTPException(status_code=422, detail="Send a JPEG up to 100 KB")
    player.avatar = image
    await session.commit()


@router.get("/me/avatar")
async def get_avatar(player: Annotated[Player, Depends(require_player)]) -> Response:
    """The logged-in player's profile photo."""
    if player.avatar is None:
        raise HTTPException(status_code=404, detail="No photo")
    return Response(player.avatar, media_type="image/jpeg")
