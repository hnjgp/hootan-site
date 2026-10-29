"""Exchange arithmetic for one position: pure Decimal math, no database and no LLM.

Isolated margin: a position can lose at most its own margin. Size is margin times
leverage; the fee is 0.05% of size when opening and again when closing.
"""

from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

START_USD = Decimal(10_000)
FEE_RATE = Decimal("0.0005")
CENT = Decimal("0.01")
SATOSHI = Decimal("0.00000001")


def cents(value: Decimal) -> Decimal:
    """Rounded to the cent."""
    return value.quantize(CENT, ROUND_HALF_UP)


def fee(margin: Decimal, leverage: int) -> Decimal:
    """Fee for opening or closing: 0.05% of the position size."""
    return cents(margin * leverage * FEE_RATE)


def max_margin(cash: Decimal, leverage: int) -> Decimal:
    """The largest margin cash can pay for, opening fee included."""
    return (cash / (1 + leverage * FEE_RATE)).quantize(CENT, ROUND_DOWN)


def quantity(margin: Decimal, leverage: int, entry: Decimal) -> Decimal:
    """BTC controlled by the position."""
    return (margin * leverage / entry).quantize(SATOSHI, ROUND_DOWN)


def liq_price(side: str, entry: Decimal, leverage: int) -> Decimal:
    """Price at which the loss equals the margin: entry x (1 -/+ 1/leverage)."""
    move = entry / leverage
    return cents(entry - move if side == "long" else entry + move)


def gross_pnl(side: str, qty: Decimal, entry: Decimal, price: Decimal) -> Decimal:
    """Profit or loss before fees; a short profits when the price falls."""
    change = price - entry
    return qty * (change if side == "long" else -change)


def trigger(
    side: str,
    price: Decimal,
    liq: Decimal,
    tp: Decimal | None,
    sl: Decimal | None,
) -> str | None:
    """Which automatic close the price reached: liq, sl, tp, or None.

    Liquidation is checked first; sl always sits before liq, so it fires first on the way.
    """
    long = side == "long"
    if price <= liq if long else price >= liq:
        return "liq"
    if sl is not None and (price <= sl if long else price >= sl):
        return "sl"
    if tp is not None and (price >= tp if long else price <= tp):
        return "tp"
    return None


def payout(margin: Decimal, pnl: Decimal, close_fee: Decimal) -> Decimal:
    """Cash returned on closing: margin plus profit minus the fee, never below zero."""
    return max(Decimal(0), cents(margin + pnl - close_fee))


def stake(margin: Decimal, pnl: Decimal) -> Decimal:
    """An open position's part of equity: its margin plus floating P&L, at least zero."""
    return max(Decimal(0), margin + pnl)


def check_levels(
    side: str, entry: Decimal, liq: Decimal, tp: Decimal | None, sl: Decimal | None
) -> str | None:
    """Why the take profit or stop loss is on the wrong side, or None when both are fine.

    A long needs tp above the entry and sl between liquidation and the entry; a short
    the mirror image.
    """
    long = side == "long"
    if tp is not None and (tp <= entry if long else tp >= entry):
        return "tp"
    if sl is not None and not (liq < sl < entry if long else entry < sl < liq):
        return "sl"
    return None
