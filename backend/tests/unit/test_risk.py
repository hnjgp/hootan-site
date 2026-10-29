from decimal import Decimal

from app.db.models import Position
from app.exchange.book import Book
from app.trading.risk import apply_pm, check_proposal
from app.trading.schema import NewPosition, PMDecision, PositionCall, TraderProposal

PRICE = Decimal(80_000)


def proposal(new: dict | None = None, calls=(), opening=True) -> TraderProposal:
    base = {
        "side": "long",
        "margin_pct": 10,
        "leverage": 2,
        "take_profit_pct": 4,
        "stop_loss_pct": 3,
    }
    return TraderProposal(
        reason="test",
        positions=[PositionCall(id=i, action=a) for i, a in calls],
        new_position=NewPosition(**base | (new or {})) if opening else None,
    )


def opened(position_id: int, margin: int = 1_000) -> Position:
    return Position(
        id=position_id,
        side="long",
        entry_price=PRICE,
        margin_usd=Decimal(margin),
        leverage=2,
        qty=Decimal("0.025"),
        liq_price=Decimal(40_000),
        fee_usd=Decimal(1),
    )


def test_an_invalid_reply_changes_nothing():
    plan = check_proposal(None, Book(), PRICE)

    assert plan.empty
    assert "invalid" in plan.notes[0]


def test_a_position_within_the_limits_is_kept_with_levels_in_prices():
    plan = check_proposal(proposal(), Book(), PRICE)

    assert plan.notes == []
    assert (plan.new.side, plan.new.margin, plan.new.leverage) == ("long", 1_000, 2)
    assert plan.new.tp_price == Decimal(83_200)
    assert plan.new.sl_price == Decimal(77_600)


def test_a_short_mirrors_its_levels():
    plan = check_proposal(proposal({"side": "short"}), Book(), PRICE)

    assert plan.new.tp_price == Decimal(76_800)
    assert plan.new.sl_price == Decimal(82_400)


def test_leverage_is_cut_to_five():
    plan = check_proposal(proposal({"leverage": 50}), Book(), PRICE)

    assert plan.new.leverage == 5
    assert "5x limit" in plan.notes[0]


def test_margin_is_cut_to_twenty_percent_of_equity():
    plan = check_proposal(proposal({"margin_pct": 60}), Book(), PRICE)

    assert plan.new.margin == 2_000
    assert "20% of equity" in plan.notes[0]


def test_margin_is_cut_to_free_cash():
    book = Book(cash=Decimal(500), open=[opened(1, margin=9_500)])

    plan = check_proposal(proposal({"margin_pct": 20}), book, PRICE)

    assert plan.new.margin == Decimal("499.50")
    assert "free cash" in plan.notes[-1]


def test_a_tiny_margin_drops_the_new_position():
    plan = check_proposal(proposal({"margin_pct": 0}), Book(), PRICE)

    assert plan.new is None
    assert "under 1 USD" in plan.notes[0]


def test_a_stop_outside_one_to_five_percent_becomes_five():
    for stop in (0, 0.5, 30):
        plan = check_proposal(proposal({"stop_loss_pct": stop}), Book(), PRICE)
        assert plan.new.sl_price == Decimal(76_000)
        assert "default 5%" in plan.notes[0]


def test_zero_take_profit_means_none():
    plan = check_proposal(proposal({"take_profit_pct": 0}), Book(), PRICE)

    assert plan.new.tp_price is None


def test_only_open_positions_can_be_closed():
    book = Book(open=[opened(7)])
    calls = [(7, "close"), (9, "close"), (7, "hold")]

    plan = check_proposal(proposal(calls=calls, opening=False), book, PRICE)

    assert plan.close == [7]
    assert "Position 9 is not open" in plan.notes[0]


def test_the_portfolio_manager_approves_rejects_or_is_skipped():
    plan = check_proposal(proposal(), Book(), PRICE)

    assert apply_pm(plan, PMDecision(reason="ok", approve=True)) is plan
    rejected = apply_pm(plan, PMDecision(reason="no", approve=False))
    assert rejected.empty and "rejected" in rejected.notes[-1]
    assert apply_pm(plan, None).empty
    nothing = check_proposal(proposal(opening=False), Book(), PRICE)
    assert apply_pm(nothing, None) is nothing
