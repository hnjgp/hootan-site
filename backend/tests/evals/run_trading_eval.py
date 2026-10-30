"""Hold 20 real meetings over 9 market/account scenarios and write
TRADING_RESULTS.md. Pass: every meeting finishes with all seven speakers and no
risk rule is broken.

Run from backend/: uv run python -m tests.evals.run_trading_eval
Each meeting runs in a transaction that is rolled back, so no real data changes.
"""

import asyncio
from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import LLMUsage, Position, SessionEvent, TradingSession
from app.db.session import engine
from app.exchange import calc
from app.exchange.book import Book, load_book, open_position
from app.llm.client import LLMClient
from app.trading.graph import describe, run_meeting
from app.trading.risk import MAX_LEVERAGE, MAX_MARGIN_SHARE, Plan

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
# Positions opened at 80,000 before the meeting: (side, margin, leverage).
ACCOUNTS = {
    "cash only": [],
    "long open": [("long", 1_500, 3)],
    "short open": [("short", 1_500, 3)],
}
SCENARIOS = [(m, a) for m in MARKETS for a in ACCOUNTS]
ENTRY = Decimal(80_000)


def violations(plan: Plan, before: Book, price: Decimal) -> list[str]:
    """Risk rules the final plan breaks; empty means it is allowed."""
    problems = []
    if set(plan.close) - {p.id for p in before.open}:
        problems.append("closed a position that was not open")
    if new := plan.new:
        if new.leverage > MAX_LEVERAGE:
            problems.append(f"leverage {new.leverage}x")
        if new.margin > before.equity(price) * MAX_MARGIN_SHARE + Decimal("0.01"):
            problems.append("margin over 20% of equity")
        if new.margin + calc.fee(new.margin, new.leverage) > before.cash:
            problems.append("spent more than cash")
        stop_pct = abs(new.sl_price / price - 1) * 100
        if not Decimal("0.99") <= stop_pct <= Decimal("5.01"):
            problems.append(f"stop {stop_pct:.2f}%")
    return problems


async def one_meeting(llm: LLMClient, n: int, market: dict, account: list) -> dict:
    """Hold one meeting in a rolled-back transaction; return what happened."""
    async with engine.connect() as conn:
        outer = await conn.begin()
        async with AsyncSession(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as db:
            # Start from the scenario alone, not the team's real open positions.
            await db.execute(delete(Position).where(Position.player_id.is_(None)))
            for side, margin, leverage in account:
                await open_position(db, None, side, Decimal(margin), leverage, ENTRY)
            before = await load_book(db, None)
            row = TradingSession(
                session_date=date(2030, 1, 1) + timedelta(days=n), status="running"
            )
            db.add(row)
            await db.commit()
            plan = await run_meeting(db, llm, row, market, before)
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
    if proposal is None:
        kind = "invalid"
    elif proposal["new_position"]:
        kind = proposal["new_position"]["side"]
    elif any(c["action"] == "close" for c in proposal["positions"]):
        kind = "close"
    else:
        kind = "wait"
    return {
        "plan": plan,
        "before": before,
        "speakers": len(events),
        "proposal": kind,
        "pm_invalid": any("invalid" in n for n in by_agent["pm"].payload["notes"]),
        "cost": cost,
    }


async def main() -> None:
    """Run every meeting, print a line each, and write TRADING_RESULTS.md."""
    llm = LLMClient(get_settings())
    async with AsyncSession(engine) as db:
        spent_before = await db.scalar(select(func.sum(LLMUsage.cost_usd))) or 0
    rows, passed, invalid, total = [], 0, 0, Decimal(0)
    kinds = Counter()
    for n in range(RUNS):
        market_name, account_name = SCENARIOS[n % len(SCENARIOS)]
        market = MARKETS[market_name]
        price = Decimal(str(market["price"]))
        r = await one_meeting(llm, n, market, ACCOUNTS[account_name])
        plan = r["plan"]
        problems = violations(plan, r["before"], price)
        if r["speakers"] != 7:
            problems.append(f"{r['speakers']} speakers")
        passed += not problems
        invalid += (r["proposal"] == "invalid") + r["pm_invalid"]
        kinds[r["proposal"]] += 1
        total += r["cost"] - spent_before
        final = describe(plan)
        mark = "PASS" if not problems else "FAIL " + "; ".join(problems)
        notes = " ".join(plan.notes) or "-"
        print(
            f"{n + 1:>2} {market_name:<5} {account_name:<10} {r['proposal']:<7} -> {final}  {mark}"
        )
        rows.append(
            f"| {n + 1} | {market_name} | {account_name} | {r['proposal']} | "
            f"{final} | {notes} | {mark} |"
        )

    summary = [
        f"- Passed: {passed}/{RUNS} ({100 * passed // RUNS}%)",
        f"- Invalid model replies (turned into no change by code): {invalid}",
        "- Trader proposals: "
        + ", ".join(
            f"{k} {kinds[k]}" for k in ("long", "short", "close", "wait", "invalid")
        ),
        f"- Cost of this run: ${total:.6f} (${total / RUNS:.6f} per meeting, with translation)",
    ]
    print("\n".join(summary))
    report = [
        "# Trading team eval results",
        "",
        (
            f"Model: {llm.settings.model_trading}. {RUNS} meetings over "
            f"{len(SCENARIOS)} market/account scenarios on the demo exchange "
            "(open positions entered at 80,000); each rolled back."
        ),
        "",
        *summary,
        "",
        "| # | Market | Account | Trader proposal | Final plan | Code notes | Result |",
        "|---|---|---|---|---|---|---|",
        *rows,
    ]
    (HERE / "TRADING_RESULTS.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
