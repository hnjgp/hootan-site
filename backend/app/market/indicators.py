"""Daily indicators for the trading team, computed in Python, never by the LLM."""

import asyncio

import pandas as pd

from app.market.prices import fetch_daily_closes, make_client


def rsi(closes: pd.Series, period: int = 14) -> float:
    """Wilder's RSI at the last close: a plain average over the first period, then smoothing."""
    change = closes.diff().dropna()
    gain = change.clip(lower=0)
    loss = -change.clip(upper=0)
    avg_gain = gain.iloc[:period].mean()
    avg_loss = loss.iloc[:period].mean()
    for up, down in zip(gain.iloc[period:], loss.iloc[period:]):
        avg_gain = (avg_gain * (period - 1) + up) / period
        avg_loss = (avg_loss * (period - 1) + down) / period
    if avg_loss == 0:
        return 100.0
    return float(100 - 100 / (1 + avg_gain / avg_loss))


def sma(closes: pd.Series, days: int) -> float:
    """Simple moving average of the last `days` closes."""
    return float(closes.iloc[-days:].mean())


def daily_indicators(closes: pd.Series) -> dict[str, float]:
    """Price, RSI(14) and 7/30-day averages from daily closes (last close = now)."""
    return {
        "price": float(closes.iloc[-1]),
        "rsi_14": round(rsi(closes), 2),
        "sma_7": round(sma(closes, 7), 2),
        "sma_30": round(sma(closes, 30), 2),
    }


async def _main() -> None:
    async with make_client() as client:
        closes = await fetch_daily_closes(client)
    print(f"{len(closes)} daily closes, last at {closes.index[-1]}")
    print(daily_indicators(closes))


if __name__ == "__main__":
    asyncio.run(_main())
