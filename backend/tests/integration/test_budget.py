from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from app.config import get_settings
from app.db.models import LLMUsage
from app.llm.budget import TEHRAN, BudgetExceeded, check_budget

SETTINGS = get_settings().model_copy(
    update={
        "ai_enabled": True,
        "budget_monthly_usd": Decimal(5),
        "budget_trading_daily_usd": Decimal("0.06"),
        "budget_public_daily_usd": Decimal("0.10"),
    }
)


async def spend(session, feature: str, cost: str, **extra) -> None:
    """Insert one usage row (ts defaults to now) and flush it so the guard sees it."""
    session.add(
        LLMUsage(
            feature=feature,
            model="gpt-5-nano",
            tokens_in=1,
            tokens_out=1,
            cost_usd=Decimal(cost),
            **extra,
        )
    )
    await session.flush()


async def test_empty_usage_allows_calls(session):
    await check_budget(session, "twin", SETTINGS)
    await check_budget(session, "trading", SETTINGS)


async def test_kill_switch_blocks_everything(session):
    off = SETTINGS.model_copy(update={"ai_enabled": False})
    with pytest.raises(BudgetExceeded):
        await check_budget(session, "twin", off)


async def test_public_cap_blocks_public_but_not_trading(session):
    await spend(session, "twin", "0.06")
    await spend(session, "embedding", "0.04")
    with pytest.raises(BudgetExceeded):
        await check_budget(session, "jobfit", SETTINGS)
    await check_budget(session, "trading", SETTINGS)


async def test_trading_cap_blocks_trading_but_not_public(session):
    await spend(session, "trading", "0.06")
    with pytest.raises(BudgetExceeded):
        await check_budget(session, "trading", SETTINGS)
    await check_budget(session, "twin", SETTINGS)


async def test_yesterday_does_not_count_for_daily_cap(session):
    yesterday = datetime.now(TEHRAN) - timedelta(days=1)
    await spend(session, "twin", "0.50", ts=yesterday)
    await check_budget(session, "twin", SETTINGS)


async def test_monthly_cap_blocks_everything(session):
    await spend(session, "jobfit", "5")
    with pytest.raises(BudgetExceeded):
        await check_budget(session, "trading", SETTINGS)
