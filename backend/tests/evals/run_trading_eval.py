"""Hold 20 real meetings over 9 market/portfolio scenarios and write
TRADING_RESULTS.md. Pass: every meeting finishes with all seven speakers and no
risk rule is broken.

Run from backend/: uv run python -m tests.evals.run_trading_eval
Each meeting runs in a transaction that is rolled back, so no real data changes.
Translation is left out; it was checked on its own (2026-10-27).
"""

import asyncio
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import LLMUsage, SessionEvent, TradingSession
from app.db.session import engine
from app.llm.client import LLMClient
from app.trading.graph import run_meeting
from app.trading.portfolio import Portfolio
from app.trading.risk import Order

HERE = Path(__file__).parent
RUNS = 20
MARKETS = {
    "crash": {
        "price": 72000.0,
        "low_24h": 71000.0,
        "high_24h": 76500.0,
        "rsi_14": 24.0,
        "sma_7": 78000.0,
        "sma_30": 81000.0,
    },
    "rally": {
        "price": 88000.0,
        "low_24h": 84500.0,
        "high_24h": 88600.0,
        "rsi_14": 76.0,
        "sma_7": 84000.0,
        "sma_30": 80000.0,
    },
    "calm": {
        "price": 80000.0,
        "low_24h": 79500.0,
        "high_24h": 80400.0,
        "rsi_14": 51.0,
        "sma_7": 79800.0,
        "sma_30": 80200.0,
    },
}
PORTFOLIOS = {
    "cash only": lambda: Portfolio(),
    "10% BTC": lambda: Portfolio(
        cash=Decimal(92_000), btc_qty=Decimal("0.1"), stop_price=Decimal(76_000)
    ),
    "20% BTC": lambda: Portfolio(
        cash=Decimal(80_000), btc_qty=Decimal("0.25"), stop_price=Decimal(76_000)
    ),
}
SCENARIOS = [(m, p) for m in MARKETS for p in PORTFOLIOS]


def violations(order: Order, before: Portfolio, price: Decimal) -> list[str]:
    """Risk rules the final order breaks; empty means it is allowed."""
    problems = []
    if order.action == "BUY":
        after = before.btc_qty + order.qty
        if after * price > before.value(price) * Decimal("0.20") + 1:
            problems.append("BTC over 20%")
        if order.qty * price > before.cash:
            problems.append("spent more than cash")
        stop_pct = (1 - order.stop_price / price) * 100
        if not Decimal(1) - Decimal("0.01") <= stop_pct <= Decimal(5) + Decimal("0.01"):
            problems.append(f"stop {stop_pct:.2f}%")
    if order.action == "SELL" and order.qty > before.btc_qty:
        problems.append("sold more than held")
    return problems


async def one_meeting(llm: LLMClient, n: int, market: dict, before: Portfolio) -> dict:
    """Hold one meeting in a rolled-back transaction; return what happened."""
    async with engine.connect() as conn:
        outer = await conn.begin()
        async with AsyncSession(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as db:
            row = TradingSession(
                session_date=date(2030, 1, 1) + timedelta(days=n), status="running"
            )
            db.add(row)
            await db.commit()
            order = await run_meeting(db, llm, row, market, before)
            events = list(
                await db.scalars(
                    select(SessionEvent)
                    .where(SessionEvent.session_id == row.id)
                    .order_by(SessionEvent.seq)
                )
            )
            cost = await db.scalar(select(func.sum(LLMUsage.cost_usd)))
        await outer.rollback()
    by_agent = {e.agent: e for e in events}
    proposal = by_agent["trader"].payload
    return {
        "order": order,
        "speakers": len(events),
        "proposal": f"{proposal['action']} {proposal['size_pct']:g}%"
        if proposal
        else "invalid",
        "pm_invalid": any("invalid" in n for n in by_agent["pm"].payload["notes"]),
        "cost": cost,
    }


async def main() -> None:
    """Run every meeting, print a line each, and write TRADING_RESULTS.md."""
    llm = LLMClient(get_settings())
    async with AsyncSession(engine) as db:
        spent_before = await db.scalar(select(func.sum(LLMUsage.cost_usd))) or 0
    rows, passed, invalid, total = [], 0, 0, Decimal(0)
    actions = Counter()
    for n in range(RUNS):
        market_name, portfolio_name = SCENARIOS[n % len(SCENARIOS)]
        market = MARKETS[market_name]
        before = PORTFOLIOS[portfolio_name]()
        price = Decimal(str(market["price"]))
        r = await one_meeting(llm, n, market, before)
        order = r["order"]
        problems = violations(order, before, price)
        if r["speakers"] != 7:
            problems.append(f"{r['speakers']} speakers")
        passed += not problems
        invalid += (r["proposal"] == "invalid") + r["pm_invalid"]
        actions[r["proposal"].split()[0]] += 1
        total += r["cost"] - spent_before
        final = (
            order.action if order.action == "HOLD" else f"{order.action} {order.qty}"
        )
        mark = "PASS" if not problems else "FAIL " + "; ".join(problems)
        notes = " ".join(order.notes) or "-"
        print(
            f"{n + 1:>2} {market_name:<5} {portfolio_name:<9} {r['proposal']:<10} -> {final:<16} {mark}"
        )
        rows.append(
            f"| {n + 1} | {market_name} | {portfolio_name} | {r['proposal']} | "
            f"{final} | {notes} | {mark} |"
        )

    summary = [
        f"- Passed: {passed}/{RUNS} ({100 * passed // RUNS}%)",
        f"- Invalid model replies (turned into HOLD by code): {invalid}",
        "- Trader proposals: "
        + ", ".join(f"{a} {actions[a]}" for a in ("BUY", "SELL", "HOLD", "invalid")),
        f"- Cost of this run: ${total:.6f} (${total / RUNS:.6f} per meeting, with translation)",
    ]
    print("\n".join(summary))
    report = [
        "# Trading team eval results",
        "",
        (
            f"Model: {llm.settings.model_trading}. {RUNS} meetings over "
            f"{len(SCENARIOS)} market/portfolio scenarios; each rolled back."
        ),
        "",
        *summary,
        "",
        "| # | Market | Portfolio | Trader proposal | Final order | Code notes | Result |",
        "|---|---|---|---|---|---|---|",
        *rows,
    ]
    (HERE / "TRADING_RESULTS.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
