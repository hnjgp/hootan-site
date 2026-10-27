import logging

from app import worker
from app.market.prices import PriceUnavailable


class FakeSession:
    """Stands in for a database session and records anything stored."""

    def __init__(self):
        self.added = []

    def add(self, row):
        self.added.append(row)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


async def test_price_job_survives_every_source_failing_and_logs_a_warning(
    monkeypatch, caplog
):
    session = FakeSession()

    async def failing_collect(_session):
        raise PriceUnavailable

    monkeypatch.setattr(worker, "SessionLocal", lambda: session)
    monkeypatch.setattr(worker, "collect_price", failing_collect)

    with caplog.at_level(logging.WARNING, logger="worker"):
        await worker.price_job()

    assert "price unavailable from every source" in caplog.text
    assert session.added == []
