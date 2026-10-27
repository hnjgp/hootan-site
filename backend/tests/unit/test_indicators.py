import pandas as pd
import pytest

from app.market.indicators import daily_indicators, rsi, sma

# Classic Wilder RSI worked example (StockCharts "cs-rsi" sheet). The sheet shows 70.53 for
# the first value because it rounds along the way; unrounded Wilder (e.g. Wickra) gives 70.46.
CLOSES = pd.Series(
    [
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89,
        46.03, 45.61, 46.28, 46.28, 46.00, 46.03, 46.41, 46.22, 45.64, 46.21, 46.25,
        45.71, 46.45, 45.78, 45.35, 44.03, 44.18, 44.22, 44.57, 43.42, 42.66, 43.13,
    ]
)  # fmt: skip


def test_rsi_matches_wilder_reference():
    assert rsi(CLOSES.iloc[:15]) == pytest.approx(70.46, abs=0.01)
    assert rsi(CLOSES.iloc[:16]) == pytest.approx(66.25, abs=0.01)
    assert rsi(CLOSES) == pytest.approx(37.79, abs=0.01)


def test_rsi_is_100_when_price_only_rises():
    assert rsi(pd.Series(range(1, 20), dtype=float)) == 100.0


def test_sma_uses_only_the_last_days():
    assert sma(pd.Series([100.0, 1.0, 2.0, 3.0]), 3) == 2.0


def test_daily_indicators_last_close_is_the_price():
    result = daily_indicators(CLOSES)
    assert result["price"] == 43.13
    assert result["rsi_14"] == 37.79
    assert result["sma_7"] == round(CLOSES.iloc[-7:].mean(), 2)
