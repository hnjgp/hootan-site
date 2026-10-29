from datetime import date
from decimal import Decimal

from app.game.scoring import settle, stake_usd, streak
from app.game.stats import players_ahead
from app.jalali import month_start, to_jalali

REF = Decimal(80_000)
STAKE = Decimal(10_000)


def test_stake_is_a_percent_of_the_balance():
    assert stake_usd(Decimal(100000), 30) == Decimal("30000.00")
    assert stake_usd(Decimal("12345.67"), 10) == Decimal("1234.57")


def test_up_wins_with_stake_times_the_move():
    out = settle("up", STAKE, REF, Decimal(81_000), ai_direction="up")
    assert out.result == "win"
    assert out.pnl_usd == Decimal("125.00")
    assert out.bonus is False


def test_down_profits_from_a_fall():
    out = settle("down", STAKE, REF, Decimal(79_200), ai_direction=None)
    assert out.result == "win"
    assert out.pnl_usd == Decimal("100.00")


def test_wrong_direction_loses_the_move():
    out = settle("up", STAKE, REF, Decimal(79_200), ai_direction="down")
    assert out.result == "lose"
    assert out.pnl_usd == Decimal("-100.00")
    assert out.bonus is False


def test_move_under_0_2_percent_is_a_draw():
    out = settle("up", STAKE, REF, Decimal(80_150), ai_direction="down")
    assert out.result == "draw"
    assert out.pnl_usd == 0


def test_exactly_0_2_percent_counts():
    assert settle("up", STAKE, REF, Decimal(80_160), None).result == "win"


def test_profit_doubles_when_the_ai_was_wrong():
    out = settle("up", STAKE, REF, Decimal(81_000), ai_direction="down")
    assert out.pnl_usd == Decimal("250.00")
    assert out.bonus is True


def test_no_bonus_without_an_ai_direction():
    out = settle("up", STAKE, REF, Decimal(81_000), ai_direction=None)
    assert out.pnl_usd == Decimal("125.00")
    assert out.bonus is False


def test_streak_counts_wins_back_from_the_newest():
    assert streak(["win", "win", "lose", "win"]) == 2
    assert streak(["win", "draw", "win"]) == 2
    assert streak(["lose", "win"]) == 0
    assert streak([]) == 0


def test_jalali_known_dates():
    assert to_jalali(date(2026, 10, 27)) == (1405, 8, 5)
    assert to_jalali(date(2026, 3, 21)) == (1405, 1, 1)
    assert to_jalali(date(2026, 3, 20)) == (1404, 12, 29)
    assert to_jalali(date(2025, 3, 20)) == (1403, 12, 30)


def test_persian_month_start():
    assert month_start(date(2026, 10, 27)) == date(2026, 10, 23)
    assert month_start(date(2026, 10, 23)) == date(2026, 10, 23)
    assert month_start(date(2026, 10, 22)) == date(2026, 9, 23)


def test_players_ahead_of_the_ai_row():
    rows = [
        {"return_pct": 3.0, "is_ai": False},
        {"return_pct": 1.0, "is_ai": True},
        {"return_pct": 1.0, "is_ai": False},
        {"return_pct": -2.0, "is_ai": False},
    ]
    assert players_ahead(rows) == (1, 3)
