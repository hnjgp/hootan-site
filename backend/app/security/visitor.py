"""Anonymous visitor id: a salted hash of the client IP, so raw IPs are never stored."""

import hashlib

from fastapi import Request

from app.config import Settings


def visitor_id(request: Request, settings: Settings) -> str:
    """Salted SHA-256 of the client IP."""
    raw = f"{settings.secret_key}:{request.client.host}"
    return hashlib.sha256(raw.encode()).hexdigest()
