"""Prompts of the trading team. Agents speak English; Persian comes from translation."""

from decimal import Decimal

from app.trading.portfolio import Portfolio

TEAM = (
    "You are part of a small AI team that trades BTC/USDT with virtual money once "
    "a day. Only BTC can be bought or sold: no shorting, no leverage, no options. "
    "If the portfolio holds no BTC, selling is not possible. Use only the numbers "
    "and comparisons you are given; do not compute new ones. Speak plainly in at "
    "most three short sentences, without bullet points."
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


def versus(price: float, average: float, days: int) -> str:
    """Where the price sits against an average, e.g. '1.7% below the 7-day average'."""
    gap = (price - average) / average * 100
    side = "above" if gap >= 0 else "below"
    return f"{abs(gap):.1f}% {side} the {days}-day average"


def market_line(market: dict) -> str:
    """The data analyst's numbers and comparisons, all computed in Python.

    gpt-5-nano misread 'price 79,728, 7-day average 81,072' as 'above the average'
    (first real meeting, 2026-10-27), so the comparisons are spelled out.
    """
    price = market["price"]
    return (
        f"BTC/USDT is {fmt(price)}; 24h range {fmt(market['low_24h'])} to "
        f"{fmt(market['high_24h'])}; RSI(14) {fmt(market['rsi_14'])}; 7-day average "
        f"{fmt(market['sma_7'])}; 30-day average {fmt(market['sma_30'])}. "
        f"The price is {versus(price, market['sma_7'], 7)} and "
        f"{versus(price, market['sma_30'], 30)}."
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
