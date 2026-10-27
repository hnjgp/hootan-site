"""The leaderboard season: the Persian month of the current trading day."""

from datetime import date, datetime, time

from app.jalali import month_start
from app.llm.budget import TEHRAN
from app.trading.run import trading_day


def season_day(now: datetime) -> date:
    """First trading day of the season."""
    return month_start(trading_day(now))


def season_start(now: datetime) -> datetime:
    """The moment the season began: 09:00 Tehran on its first day."""
    return datetime.combine(season_day(now), time(9), TEHRAN)
