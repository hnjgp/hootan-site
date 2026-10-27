"""Signed player cookie: the player id plus an HMAC only the server can make."""

import hashlib
import hmac
import uuid

from fastapi import Response

from app.config import Settings

COOKIE_NAME = "player"
MAX_AGE = 365 * 24 * 3600


def sign(player_id: uuid.UUID, settings: Settings) -> str:
    """Cookie value `<uuid>.<hmac>`."""
    mac = hmac.new(
        settings.secret_key.encode(), str(player_id).encode(), hashlib.sha256
    )
    return f"{player_id}.{mac.hexdigest()}"


def unsign(value: str, settings: Settings) -> uuid.UUID | None:
    """The player id if the signature matches, else None."""
    raw, _, _ = value.partition(".")
    try:
        player_id = uuid.UUID(raw)
    except ValueError:
        return None
    return player_id if hmac.compare_digest(sign(player_id, settings), value) else None


def set_player_cookie(
    response: Response, player_id: uuid.UUID, settings: Settings
) -> None:
    """Store the signed id for a year: HttpOnly, Secure, SameSite=Lax."""
    response.set_cookie(
        COOKIE_NAME,
        sign(player_id, settings),
        max_age=MAX_AGE,
        httponly=True,
        secure=True,
        samesite="lax",
    )
