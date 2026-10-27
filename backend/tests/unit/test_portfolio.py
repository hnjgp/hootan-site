from decimal import Decimal

from app.db.models import PortfolioTrade
from app.trading.portfolio import INITIAL_CASH, Portfolio, from_trades, hold_value


def trade(side: str, qty: str, price: str, stop: str | None = None) -> PortfolioTrade:
    return PortfolioTrade(
        side=side,
        qty=Decimal(qty),
        price=Decimal(price),
        stop_price=Decimal(stop) if stop else None,
        reason="test",
    )


def test_no_trades_is_all_cash():
    p = from_trades([])
    assert (p.cash, p.btc_qty, p.stop_price) == (INITIAL_CASH, 0, None)


def test_buy_then_partial_sell():
    p = from_trades(
        [trade("BUY", "0.25", "80000", "76000"), trade("SELL", "0.1", "82000")]
    )
    assert p.cash == Decimal(100_000) - Decimal(20_000) + Decimal(8_200)
    assert p.btc_qty == Decimal("0.15")
    assert p.stop_price == Decimal(76_000)
    assert p.value(Decimal(82_000)) == p.cash + Decimal("0.15") * 82_000


def test_selling_everything_clears_the_stop():
    p = from_trades(
        [trade("BUY", "0.1", "80000", "76000"), trade("SELL", "0.1", "75000")]
    )
    assert p.btc_qty == 0
    assert p.stop_price is None


def test_stop_hit_only_with_a_position_at_or_below_the_stop():
    p = Portfolio(btc_qty=Decimal("0.1"), stop_price=Decimal(76_000))
    assert p.stop_hit(Decimal(76_000))
    assert not p.stop_hit(Decimal(76_001))
    assert not Portfolio().stop_hit(Decimal(1))


def test_hold_value_follows_the_price_from_the_first_session():
    assert hold_value(Decimal(80_000), Decimal(88_000)) == Decimal(110_000)
