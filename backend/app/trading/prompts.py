"""Prompts of the trading team. Agents speak English; Persian comes from translation."""

from decimal import Decimal

from app.db.models import Position
from app.exchange.book import Book, pnl

TEAM = (
    "You are part of a small AI team that trades BTC/USDT with virtual money on a "
    "demo exchange, meeting once a day. The team can open long positions (profit "
    "when BTC rises) or short positions (profit when it falls), with leverage up to "
    "5x, and close open positions. Each position has its own margin; a stop loss "
    "closes it automatically, and at the liquidation price the whole margin is lost. "
    "Opening and closing each cost a 0.05% fee on the position size. Use only the "
    "numbers and comparisons you are given; do not compute new ones. Speak plainly "
    "in at most three short sentences, without bullet points."
)

ROLES = {
    "bull": "You are the bull. Make the strongest honest case that BTC will rise: "
    "for a long position, or for closing short positions.",
    "bear": "You are the bear. Make the strongest honest case that BTC will fall: "
    "for a short position, or for closing long positions.",
    # In the first eval (2026-10-27) the trader chose BUY 20 times out of 20, even
    # with RSI 76, so every choice is described here. On the exchange (2026-10-30) it
    # still opened 10 longs and 1 short, so long and short get mirror-image rules.
    "trader": "You are the trader. Weigh the bull and the bear fairly. For every "
    "open position choose hold or close: close when the case has turned against it. "
    "Then open at most one new position, only when one side is clearly stronger. "
    "Long and short are equally normal trades; do not prefer long. Go short when "
    "BTC is overbought (RSI above 70) after a rally, or when it trades below both "
    "averages and is not oversold (RSI above 30). Go long when BTC is oversold (RSI "
    "below 30) after a fall, or when it trades above both averages and is not "
    "overbought (RSI below 70). Otherwise set new_position to null; "
    "doing nothing is a normal and often correct choice. margin_pct is the percent "
    "of equity put up as margin (the limit is 20); leverage 1 to 5, lower when "
    "unsure; stop_loss_pct 1 to 5; take_profit_pct is the price move at which to "
    "take profit, or 0 for none.",
    "risk": "You are the risk manager. Code has already checked the trader's "
    "plan against the risk rules. Explain the checked plan and any rule that "
    "changed it.",
    "pm": "You are the portfolio manager and make the final call. Approve or reject "
    "the checked plan as a whole.",
}


def fmt(value: float | Decimal | None) -> str:
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


def position_line(p: Position, price: Decimal) -> str:
    """One open position with its floating result."""
    tp = fmt(p.tp_price) if p.tp_price else "none"
    return (
        f"#{p.id} {p.side} {p.leverage}x, entry {fmt(p.entry_price)}, margin "
        f"{fmt(p.margin_usd)} USD, floating P&L {fmt(pnl(p, price))} USD, take "
        f"profit {tp}, stop loss {fmt(p.sl_price)}, liquidation {fmt(p.liq_price)}"
    )


def book_line(book: Book, price: Decimal) -> str:
    """Equity, free cash and every open position."""
    lines = [
        f"Account: {fmt(book.equity(price))} USD equity, {fmt(book.cash)} USD free cash."
    ]
    if book.open:
        lines.append("Open positions:")
        lines += [position_line(p, price) for p in book.open]
    else:
        lines.append("No open positions.")
    return "\n".join(lines)


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
