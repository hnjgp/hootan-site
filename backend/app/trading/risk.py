"""Risk rules in code: the model proposes, these functions decide what is allowed.

Every rule that changes a proposal adds a note, so the session log shows it.
One trade per day needs no rule here: there is one session per trading day.
"""

from dataclasses import dataclass, field
from decimal import ROUND_DOWN, Decimal

from app.trading.portfolio import Portfolio
from app.trading.schema import PMDecision, TraderProposal

MAX_BTC_SHARE = Decimal("0.20")
DEFAULT_STOP_PCT = Decimal(5)
MIN_STOP_PCT = Decimal(1)
SATOSHI = Decimal("0.00000001")


@dataclass
class Order:
    """What the code allows: action, BTC quantity, stop price and why it changed."""

    action: str
    qty: Decimal = Decimal(0)
    stop_price: Decimal | None = None
    notes: list[str] = field(default_factory=list)


def hold(note: str) -> Order:
    """A HOLD order with the reason it became one."""
    return Order("HOLD", notes=[note])


def check_proposal(
    proposal: TraderProposal | None, portfolio: Portfolio, price: Decimal
) -> Order:
    """Turn the trader's proposal into an allowed order; None means an invalid reply."""
    if proposal is None:
        return hold("Trader reply was invalid, so the order is HOLD.")
    if proposal.action == "HOLD":
        return Order("HOLD")

    pct = Decimal(str(proposal.size_pct)) / 100
    if proposal.action == "SELL":
        if portfolio.btc_qty == 0:
            return hold("SELL rejected: there is no BTC to sell.")
        qty = (portfolio.btc_qty * pct).quantize(SATOSHI, ROUND_DOWN)
        return Order("SELL", qty) if qty > 0 else hold("SELL size was zero.")

    value = portfolio.value(price)
    wanted = value * pct
    room = min(value * MAX_BTC_SHARE - portfolio.btc_qty * price, portfolio.cash)
    notes = []
    if wanted > room:
        notes.append(
            f"BUY of {proposal.size_pct:g}% cut to stay within the 20% BTC limit."
        )
    qty = (min(wanted, room) / price).quantize(SATOSHI, ROUND_DOWN)
    if qty <= 0:
        return hold("BUY rejected: BTC is already at the 20% limit.")
    return Order("BUY", qty, notes=notes)


def apply_pm(order: Order, decision: PMDecision | None, price: Decimal) -> Order:
    """Final order after the portfolio manager; a BUY gets a stop between 1% and 5%."""
    if order.action == "HOLD":
        return order
    if decision is None:
        return hold("Portfolio manager reply was invalid, so the order is HOLD.")
    if not decision.approve:
        return hold("Portfolio manager rejected the order.")
    if order.action == "BUY":
        pct = Decimal(str(decision.stop_loss_pct))
        if not MIN_STOP_PCT <= pct <= DEFAULT_STOP_PCT:
            order.notes.append(f"Stop loss of {pct}% replaced by the default 5%.")
            pct = DEFAULT_STOP_PCT
        order.stop_price = (price * (1 - pct / 100)).quantize(Decimal("0.01"))
    return order
