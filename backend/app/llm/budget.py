"""Budget guard: checks spending in llm_usage against the caps before any LLM call."""

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import LLMUsage

TEHRAN = ZoneInfo("Asia/Tehran")
PUBLIC_FEATURES = ("twin", "jobfit", "embedding")


class BudgetExceeded(Exception):
    """AI is switched off or a spending cap is reached; the call must not be made."""


def day_and_month_start(now: datetime) -> tuple[datetime, datetime]:
    """Start of today and of this month on the Asia/Tehran calendar."""
    day_start = now.astimezone(TEHRAN).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return day_start, day_start.replace(day=1)


async def spent_since(
    session: AsyncSession, start: datetime, features: tuple[str, ...] | None = None
) -> Decimal:
    """Total cost in USD since `start`, optionally only for the given features."""
    query = select(func.coalesce(func.sum(LLMUsage.cost_usd), 0)).where(
        LLMUsage.ts >= start
    )
    if features:
        query = query.where(LLMUsage.feature.in_(features))
    return await session.scalar(query)


async def check_budget(session: AsyncSession, feature: str, settings: Settings) -> None:
    """Raise BudgetExceeded if AI is off or the monthly or daily cap is used up.

    Days and months follow the Asia/Tehran calendar. Trading has its own daily cap;
    every other feature shares the public daily cap.
    """
    if not settings.ai_enabled:
        raise BudgetExceeded("AI is disabled")

    day_start, month_start = day_and_month_start(datetime.now(TEHRAN))
    if await spent_since(session, month_start) >= settings.budget_monthly_usd:
        raise BudgetExceeded("monthly budget reached")

    if feature == "trading":
        cap, features = settings.budget_trading_daily_usd, ("trading",)
    else:
        cap, features = settings.budget_public_daily_usd, PUBLIC_FEATURES
    if await spent_since(session, day_start, features) >= cap:
        raise BudgetExceeded(f"daily {feature} budget reached")
