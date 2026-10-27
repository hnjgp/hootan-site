"""The AI team's virtual portfolio, rebuilt from its trades like a bank statement."""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PortfolioTrade

INITIAL_CASH = Decimal(100_000)


@dataclass
class Portfolio:
    """Cash, BTC held and the stop price of the open position (None when flat)."""

    cash: Decimal = INITIAL_CASH
    btc_qty: Decimal = Decimal(0)
    stop_price: Decimal | None = None

    def value(self, price: Decimal) -> Decimal:
        """Total value in USD at the given BTC price."""
        return self.cash + self.btc_qty * price

    def stop_hit(self, price: Decimal) -> bool:
        """True when BTC is held and the price fell to the stop or below."""
        return (
            self.btc_qty > 0
            and self.stop_price is not None
            and price <= self.stop_price
        )


def from_trades(trades: list[PortfolioTrade]) -> Portfolio:
    """Apply the trades oldest first; the last buy sets the stop, selling everything clears it."""
    p = Portfolio()
    for t in trades:
        if t.side == "BUY":
            p.cash -= t.qty * t.price
            p.btc_qty += t.qty
            p.stop_price = t.stop_price
        else:
            p.cash += t.qty * t.price
            p.btc_qty -= t.qty
            if p.btc_qty == 0:
                p.stop_price = None
    return p


async def load_portfolio(session: AsyncSession) -> Portfolio:
    """Current portfolio from every trade in the database."""
    trades = await session.scalars(select(PortfolioTrade).order_by(PortfolioTrade.id))
    return from_trades(list(trades))


def hold_value(first_price: Decimal, price: Decimal) -> Decimal:
    """Value of the starting cash had it all bought BTC at the first session's price."""
    return INITIAL_CASH / first_price * price
