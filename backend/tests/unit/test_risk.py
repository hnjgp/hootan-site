from decimal import Decimal

from app.trading.portfolio import Portfolio
from app.trading.risk import Order, apply_pm, check_proposal
from app.trading.schema import PMDecision, TraderProposal

PRICE = Decimal(80_000)


def proposal(action: str, size: float) -> TraderProposal:
    return TraderProposal(reason="test", action=action, size_pct=size)


def pm(approve: bool = True, stop: float = 3) -> PMDecision:
    return PMDecision(reason="test", approve=approve, stop_loss_pct=stop)


def test_invalid_reply_is_hold():
    order = check_proposal(None, Portfolio(), PRICE)
    assert order.action == "HOLD"
    assert "invalid" in order.notes[0]


def test_buy_within_the_limit_is_kept():
    order = check_proposal(proposal("BUY", 10), Portfolio(), PRICE)
    assert order.action == "BUY"
    assert order.qty == Decimal("0.125")
    assert order.notes == []


def test_buy_over_20_percent_is_cut_and_logged():
    order = check_proposal(proposal("BUY", 100), Portfolio(), PRICE)
    assert order.qty == Decimal("0.25")
    assert "20%" in order.notes[0]


def test_buy_counts_btc_already_held():
    held = Portfolio(cash=Decimal(92_000), btc_qty=Decimal("0.1"))
    order = check_proposal(proposal("BUY", 50), held, PRICE)
    assert order.qty == Decimal("0.15")


def test_buy_of_zero_percent_is_hold_with_the_true_reason():
    """Eval 2026-10-27: 'BUY 0%' with cash only was logged as 'already at 20%'."""
    order = check_proposal(proposal("BUY", 0), Portfolio(), PRICE)
    assert order.action == "HOLD"
    assert "zero" in order.notes[0]


def test_buy_at_the_limit_becomes_hold():
    full = Portfolio(cash=Decimal(80_000), btc_qty=Decimal("0.25"))
    assert check_proposal(proposal("BUY", 10), full, PRICE).action == "HOLD"


def test_sell_without_btc_becomes_hold():
    order = check_proposal(proposal("SELL", 50), Portfolio(), PRICE)
    assert order.action == "HOLD"
    assert "no BTC" in order.notes[0]


def test_sell_is_a_share_of_the_btc_held():
    held = Portfolio(cash=Decimal(92_000), btc_qty=Decimal("0.1"))
    order = check_proposal(proposal("SELL", 50), held, PRICE)
    assert (order.action, order.qty) == ("SELL", Decimal("0.05"))


def test_pm_rejection_or_invalid_reply_is_hold():
    assert (
        apply_pm(Order("BUY", Decimal("0.1")), pm(approve=False), PRICE).action
        == "HOLD"
    )
    assert apply_pm(Order("BUY", Decimal("0.1")), None, PRICE).action == "HOLD"


def test_pm_stop_is_used_when_between_1_and_5_percent():
    order = apply_pm(Order("BUY", Decimal("0.1")), pm(stop=3), PRICE)
    assert order.stop_price == Decimal(77_600)


def test_pm_stop_outside_the_range_becomes_5_percent():
    order = apply_pm(Order("BUY", Decimal("0.1")), pm(stop=30), PRICE)
    assert order.stop_price == Decimal(76_000)
    assert "default 5%" in order.notes[0]


def test_sell_has_no_stop():
    order = apply_pm(Order("SELL", Decimal("0.1")), pm(), PRICE)
    assert (order.action, order.stop_price) == ("SELL", None)
