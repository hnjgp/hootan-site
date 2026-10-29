"""Risk rules in code: the model proposes, these functions decide what is allowed.

Every rule that changes a proposal adds a note, so the session log shows it.
At most one new position a day needs no rule here: the schema allows one and
there is one session per trading day.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from app.exchange import calc
from app.exchange.book import Book
from app.trading.schema import PMDecision, TraderProposal

MAX_LEVERAGE = 5
MAX_MARGIN_SHARE = Decimal("0.20")
DEFAULT_STOP_PCT = Decimal(5)
MIN_STOP_PCT = Decimal(1)


@dataclass
class NewOrder:
    """A position the code allows the team to open, levels already in prices."""

    side: str
    margin: Decimal
    leverage: int
    tp_price: Decimal | None
    sl_price: Decimal


@dataclass
class Plan:
    """What the code allows: open positions to close, at most one to open, and why
    the proposal changed."""

    close: list[int] = field(default_factory=list)
    new: NewOrder | None = None
    notes: list[str] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        """True when the plan changes nothing."""
        return not self.close and self.new is None


def level(price: Decimal, pct: Decimal, side: str, up: bool) -> Decimal:
    """Price `pct` percent away from `price`, above when `up` for a long (mirrored for a short)."""
    sign = 1 if up == (side == "long") else -1
    return calc.cents(price * (1 + sign * pct / 100))


def check_proposal(proposal: TraderProposal | None, book: Book, price: Decimal) -> Plan:
    """Turn the trader's proposal into an allowed plan; None means an invalid reply."""
    if proposal is None:
        return Plan(notes=["Trader reply was invalid, so nothing changes."])
    plan = Plan()
    open_ids = {p.id for p in book.open}
    for call in proposal.positions:
        if call.action != "close":
            continue
        if call.id in open_ids:
            plan.close.append(call.id)
        else:
            plan.notes.append(
                f"Position {call.id} is not open, so it cannot be closed."
            )
    new = proposal.new_position
    if new is None:
        return plan

    leverage = new.leverage
    if leverage > MAX_LEVERAGE:
        plan.notes.append(f"Leverage of {leverage}x cut to the {MAX_LEVERAGE}x limit.")
        leverage = MAX_LEVERAGE
    equity = book.equity(price)
    margin = equity * Decimal(str(new.margin_pct)) / 100
    if margin > equity * MAX_MARGIN_SHARE:
        plan.notes.append(
            f"Margin of {new.margin_pct:g}% cut to the 20% of equity limit."
        )
        margin = equity * MAX_MARGIN_SHARE
    if margin > calc.max_margin(book.cash, leverage):
        plan.notes.append("Margin cut to the free cash.")
        margin = calc.max_margin(book.cash, leverage)
    margin = calc.cents(margin)
    if margin < 1:
        plan.notes.append("New position dropped: its margin was under 1 USD.")
        return plan

    stop = Decimal(str(new.stop_loss_pct))
    if not MIN_STOP_PCT <= stop <= DEFAULT_STOP_PCT:
        plan.notes.append(f"Stop loss of {stop}% replaced by the default 5%.")
        stop = DEFAULT_STOP_PCT
    tp = Decimal(str(new.take_profit_pct))
    plan.new = NewOrder(
        side=new.side,
        margin=margin,
        leverage=leverage,
        tp_price=level(price, tp, new.side, up=True) if tp > 0 else None,
        sl_price=level(price, stop, new.side, up=False),
    )
    return plan


def apply_pm(plan: Plan, decision: PMDecision | None) -> Plan:
    """Final plan after the portfolio manager; a rejection or invalid reply changes nothing."""
    if plan.empty:
        return plan
    if decision is None:
        return Plan(notes=plan.notes + ["Portfolio manager reply was invalid."])
    if not decision.approve:
        return Plan(notes=plan.notes + ["Portfolio manager rejected the plan."])
    return plan
