"""In-memory per-IP rate limiting for public endpoints (one server, so no Redis)."""

import time
from collections import defaultdict, deque
from collections.abc import Callable
from datetime import timedelta

from fastapi import HTTPException, Request


class RateLimiter:
    """Sliding window: at most `limit` hits per `window` for each key."""

    def __init__(
        self, limit: int, window: timedelta, clock: Callable[[], float] = time.monotonic
    ):
        self.limit = limit
        self.window = window.total_seconds()
        self.clock = clock
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def _current(self, key: str) -> deque[float]:
        """The key's hits still inside the window."""
        hits = self.hits[key]
        while hits and hits[0] <= self.clock() - self.window:
            hits.popleft()
        return hits

    def allow(self, key: str) -> bool:
        """Record a hit and return True, or return False if the key is over the limit."""
        hits = self._current(key)
        if len(hits) >= self.limit:
            return False
        hits.append(self.clock())
        return True

    def remaining(self, key: str) -> int:
        """How many hits the key has left in the current window."""
        return self.limit - len(self._current(key))


def limit_by_ip(*limiters: RateLimiter) -> Callable[[Request], None]:
    """FastAPI dependency that answers 429 when any limiter rejects the client IP."""

    def dependency(request: Request) -> None:
        ip = request.client.host
        if not all(limiter.allow(ip) for limiter in limiters):
            raise HTTPException(status_code=429, detail="Too many requests")

    return dependency
