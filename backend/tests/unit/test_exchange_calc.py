from decimal import Decimal

import pytest

from app.exchange import calc

ENTRY = Decimal(80_000)


def test_fee_is_five_hundredths_of_a_percent_of_the_size():
    assert calc.fee(Decimal(1_000), 10) == Decimal("5.00")
    assert calc.fee(Decimal(100), 1) == Decimal("0.05")


def test_max_margin_leaves_room_for_the_opening_fee():
    margin = calc.max_margin(Decimal(10_000), 10)

    assert margin + calc.fee(margin, 10) <= 10_000
    assert margin == Decimal("9950.24")


def test_quantity_is_margin_times_leverage_over_the_entry():
    assert calc.quantity(Decimal(1_000), 8, ENTRY) == Decimal("0.1")


@pytest.mark.parametrize(
    ("side", "leverage", "expected"),
    [
        ("long", 10, 72_000),
        ("short", 10, 88_000),
        ("long", 100, 79_200),
        ("short", 1, 160_000),
        ("long", 1, 0),
    ],
)
def test_liquidation_is_where_the_loss_equals_the_margin(side, leverage, expected):
    liq = calc.liq_price(side, ENTRY, leverage)

    assert liq == expected
    margin = Decimal(1_000)
    qty = calc.quantity(margin, leverage, ENTRY)
    assert calc.gross_pnl(side, qty, ENTRY, liq) == pytest.approx(-margin, abs=0.01)


def test_a_short_profits_when_the_price_falls():
    qty = Decimal("0.1")

    assert calc.gross_pnl("short", qty, ENTRY, Decimal(78_000)) == 200
    assert calc.gross_pnl("long", qty, ENTRY, Decimal(78_000)) == -200


@pytest.mark.parametrize(
    ("side", "price", "expected"),
    [
        ("long", 85_000, "tp"),
        ("long", 77_000, "sl"),
        ("long", 72_000, "liq"),
        ("long", 79_000, None),
        ("short", 75_000, "tp"),
        ("short", 83_000, "sl"),
        ("short", 88_500, "liq"),
        ("short", 81_000, None),
    ],
)
def test_trigger_checks_liquidation_then_stop_then_take_profit(side, price, expected):
    long = side == "long"
    liq = Decimal(72_000 if long else 88_000)
    tp = Decimal(85_000 if long else 75_000)
    sl = Decimal(77_000 if long else 83_000)

    assert calc.trigger(side, Decimal(price), liq, tp, sl) == expected


def test_without_levels_only_liquidation_fires():
    assert calc.trigger("long", Decimal(1), Decimal(72_000), None, None) == "liq"
    assert calc.trigger("long", Decimal(99_000), Decimal(72_000), None, None) is None


def test_payout_is_margin_plus_profit_minus_fee_and_never_negative():
    assert calc.payout(Decimal(1_000), Decimal(250), Decimal(5)) == Decimal(1_245)
    assert calc.payout(Decimal(1_000), Decimal(-1_200), Decimal(5)) == 0


def test_stake_never_goes_below_zero():
    assert calc.stake(Decimal(1_000), Decimal(-300)) == 700
    assert calc.stake(Decimal(1_000), Decimal(-1_300)) == 0


@pytest.mark.parametrize(
    ("side", "tp", "sl", "problem"),
    [
        ("long", 85_000, 77_000, None),
        ("long", 79_000, None, "tp"),
        ("long", None, 81_000, "sl"),
        ("long", None, 70_000, "sl"),
        ("short", 75_000, 83_000, None),
        ("short", 81_000, None, "tp"),
        ("short", None, 79_000, "sl"),
        ("short", None, 90_000, "sl"),
        ("long", None, None, None),
    ],
)
def test_levels_must_sit_on_the_right_side(side, tp, sl, problem):
    liq = calc.liq_price(side, ENTRY, 10)
    to_dec = lambda v: None if v is None else Decimal(v)

    assert calc.check_levels(side, ENTRY, liq, to_dec(tp), to_dec(sl)) == problem
