"""Prompts of the trading team. Agents speak English; Persian comes from translation."""

from decimal import Decimal

from app.trading.portfolio import Portfolio

TEAM = (
    "You are part of a small AI team that trades BTC/USDT with virtual money once "
    "a day. Only BTC can be bought or sold: no shorting, no leverage, no options. "
    "Use the numbers you are given. Speak plainly in at most three short sentences."
)

ROLES = {
    "bull": "You are the bull. Make the strongest honest case for buying BTC today.",
    "bear": "You are the bear. Make the strongest honest case against buying, "
    "or for selling the BTC held.",
    "trader": "You are the trader. Weigh the bull and the bear and propose one "
    "action. size_pct: for BUY, percent of the total portfolio value to spend; "
    "for SELL, percent of the BTC held to sell; 0 for HOLD. Code caps BTC at 20% "
    "of the portfolio.",
    "risk": "You are the risk manager. Code has already checked the trader's "
    "proposal against the risk rules. Explain the checked order and any rule that "
    "changed it.",
    "pm": "You are the portfolio manager and make the final call. Approve or reject "
    "the checked order. For a BUY choose stop_loss_pct between 1 and 5.",
}


def fmt(value: float | None) -> str:
    """A number with thousands separators, or n/a when missing."""
    return "n/a" if value is None else f"{value:,.2f}"


def market_line(market: dict) -> str:
    """One sentence with the data analyst's numbers."""
    return (
        f"BTC/USDT is {fmt(market['price'])}; 24h range {fmt(market['low_24h'])} to "
        f"{fmt(market['high_24h'])}; RSI(14) {fmt(market['rsi_14'])}; 7-day average "
        f"{fmt(market['sma_7'])}; 30-day average {fmt(market['sma_30'])}."
    )


def portfolio_line(portfolio: Portfolio, price: Decimal) -> str:
    """Cash, BTC held and the BTC share of the portfolio."""
    value = portfolio.value(price)
    share = portfolio.btc_qty * price / value * 100
    return (
        f"Portfolio: {fmt(value)} USD in total, {fmt(portfolio.cash)} USD cash, "
        f"{portfolio.btc_qty} BTC ({share:.1f}% of the portfolio)."
    )


def messages(
    role: str, briefing: str, transcript: list[str], extra: str = ""
) -> list[dict]:
    """System prompt for the role; the briefing, the meeting so far and any extra facts."""
    user = briefing + "\n\nMeeting so far:\n" + "\n".join(transcript)
    if extra:
        user += "\n\n" + extra
    return [
        {"role": "system", "content": f"{TEAM} {ROLES[role]}"},
        {"role": "user", "content": user},
    ]
