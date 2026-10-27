"""Settling a prediction: pure arithmetic, no database and no LLM (CLAUDE.md 4.2)."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# A move smaller than 0.2% is a draw: nobody wins or loses.
DEAD_ZONE = Decimal("0.002")
CENT = Decimal("0.01")
# The team's decision as a direction; HOLD has none, so it gives no bonus.
AI_DIRECTION = {"BUY": "up", "SELL": "down"}


@dataclass
class Outcome:
    """Result of one prediction and the USD it adds to (or takes from) the wallet."""

    result: str
    pnl_usd: Decimal
    bonus: bool


def stake_usd(balance: Decimal, pct: int) -> Decimal:
    """USD put in play: pct percent of the balance, to the cent."""
    return (balance * pct / 100).quantize(CENT, ROUND_HALF_UP)


def settle(
    direction: str,
    stake: Decimal,
    ref_price: Decimal,
    price: Decimal,
    ai_direction: str | None,
) -> Outcome:
    """Win, lose or draw against the reference price; profit doubles when the AI was wrong.

    P&L is stake times the percent move ("down" profits from a fall); a loss is never doubled.
    """
    change = (price - ref_price) / ref_price
    if abs(change) < DEAD_ZONE:
        return Outcome("draw", Decimal(0), False)
    moved = "up" if change > 0 else "down"
    pnl = stake * (change if direction == "up" else -change)
    if moved != direction:
        return Outcome("lose", pnl.quantize(CENT, ROUND_HALF_UP), False)
    bonus = ai_direction is not None and ai_direction != direction
    if bonus:
        pnl *= 2
    return Outcome("win", pnl.quantize(CENT, ROUND_HALF_UP), bonus)


def streak(results: list[str]) -> int:
    """Wins in a row counting back from the newest result; draws neither add nor break."""
    count = 0
    for result in results:
        if result == "lose":
            break
        if result == "win":
            count += 1
    return count
