"""Forgotten password: a 6-digit code by email, then the code and a new password.

The code is stored only as a hash, lasts 15 minutes and works once. The forgot
answer is the same whether or not the email is registered.
"""

import asyncio
import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import Player
from app.db.session import get_session
from app.game.accounts import Password
from app.game.api import check_limit, me_out, shown_price
from app.mail import send_mail
from app.security.cookie import set_player_cookie
from app.security.rate_limit import RateLimiter

router = APIRouter(prefix="/api/game/password")
log = logging.getLogger("password")

FORGOT_LIMITER = RateLimiter(5, timedelta(hours=1))
# A million codes against ten tries an hour: guessing one in 15 minutes is hopeless.
RESET_LIMITER = RateLimiter(10, timedelta(hours=1))
CODE_LIFETIME = timedelta(minutes=15)

MAIL = {
    "en": (
        "Your password reset code",
        (
            "Hi {nickname},\n\nYour code is {code}. It works once, for 15 minutes.\n\n"
            "If you did not ask for it, ignore this email.\n\nhootanseifi.pro"
        ),
    ),
    "fa": (
        "کد بازیابی رمز",
        (
            "سلام {nickname}،\n\nکد شما {code} است. فقط یک بار و تا 15 دقیقه کار می‌کند.\n\n"
            "اگر شما درخواست نکرده‌اید، این ایمیل را نادیده بگیرید.\n\nhootanseifi.pro"
        ),
    ),
}


class Forgot(BaseModel):
    email: EmailStr
    lang: Literal["en", "fa"] = "en"


class Reset(BaseModel):
    email: EmailStr
    code: Annotated[str, Field(pattern=r"^\d{6}$")]
    password: Password
    remember: bool = False


def code_hash(code: str, settings: Settings) -> str:
    """HMAC of the code, so a leaked database does not reveal live codes."""
    return hmac.new(
        settings.secret_key.encode(), code.encode(), hashlib.sha256
    ).hexdigest()


async def by_email(session: AsyncSession, email: str) -> Player | None:
    """The player with this email, ignoring case."""
    return await session.scalar(
        select(Player).where(func.lower(Player.email) == email.lower())
    )


@router.post("/forgot", status_code=204)
async def forgot(
    body: Forgot,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Email a fresh code with the nickname; a failed send is only logged."""
    check_limit(FORGOT_LIMITER, request)
    player = await by_email(session, body.email)
    if player is None:
        return
    settings = get_settings()
    code = f"{secrets.randbelow(10**6):06d}"
    player.reset_code_hash = code_hash(code, settings)
    player.reset_expires_at = datetime.now(UTC) + CODE_LIFETIME
    await session.commit()
    subject, text = MAIL[body.lang]
    try:
        await asyncio.to_thread(
            send_mail,
            settings,
            player.email,
            subject,
            text.format(nickname=player.nickname, code=code),
        )
    except OSError:
        log.exception("reset email to player %s failed", player.id)


@router.post("/reset")
async def reset(
    body: Reset,
    request: Request,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    price: Annotated[Decimal, Depends(shown_price)],
) -> dict:
    """Set the new password and log in; 400 for a wrong, used or expired code."""
    check_limit(RESET_LIMITER, request)
    settings = get_settings()
    player = await by_email(session, body.email)
    valid = (
        player is not None
        and player.reset_code_hash is not None
        and player.reset_expires_at > datetime.now(UTC)
        and hmac.compare_digest(player.reset_code_hash, code_hash(body.code, settings))
    )
    if not valid:
        raise HTTPException(status_code=400, detail="Wrong or expired code")
    player.password = body.password
    player.reset_code_hash = player.reset_expires_at = None
    await session.commit()
    set_player_cookie(response, player.id, settings, body.remember)
    return await me_out(session, player, price)
