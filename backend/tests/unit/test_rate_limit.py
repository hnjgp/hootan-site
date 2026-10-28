from datetime import timedelta

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.security.rate_limit import RateLimiter, limit_by_ip


class FakeClock:
    """Clock the test moves by hand instead of waiting."""

    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_blocks_after_limit_and_frees_after_window():
    clock = FakeClock()
    limiter = RateLimiter(2, timedelta(minutes=10), clock)

    assert limiter.allow("a")
    assert limiter.allow("a")
    assert not limiter.allow("a")

    clock.now = 10 * 60
    assert limiter.allow("a")


def test_each_key_has_its_own_count():
    limiter = RateLimiter(1, timedelta(minutes=10), FakeClock())

    assert limiter.allow("a")
    assert limiter.allow("b")
    assert not limiter.allow("a")


def test_remaining_counts_down_and_refills_after_window():
    clock = FakeClock()
    limiter = RateLimiter(2, timedelta(minutes=10), clock)

    assert limiter.remaining("a") == 2
    limiter.allow("a")
    limiter.allow("a")
    assert limiter.remaining("a") == 0

    clock.now = 10 * 60
    assert limiter.remaining("a") == 2


def test_endpoint_returns_429_over_limit():
    app = FastAPI()
    limiter = RateLimiter(2, timedelta(minutes=10), FakeClock())

    @app.get("/ping", dependencies=[Depends(limit_by_ip(limiter))])
    def ping() -> dict[str, str]:
        return {"ok": "yes"}

    client = TestClient(app)
    codes = [client.get("/ping").status_code for _ in range(3)]

    assert codes == [200, 200, 429]
