from decimal import Decimal

import pytest

from app.llm.pricing import cost_usd


def test_smoke_call_cost():
    # Real numbers from the AvalAI smoke test: 12 in, 74 out (64 of them reasoning).
    assert cost_usd("gpt-5-nano", 12, 74) == Decimal("0.000030")


def test_one_million_tokens_each_way():
    assert cost_usd("gemini-2.5-flash", 1_000_000, 1_000_000) == Decimal("2.800000")


def test_unknown_model_fails_loudly():
    with pytest.raises(KeyError):
        cost_usd("no-such-model", 1, 1)


def test_cached_input_is_cheaper():
    # 7000 in (6000 cached), 500 out on gpt-4.1-mini: 1000*0.40 + 6000*0.10 + 500*1.60.
    assert cost_usd("gpt-4.1-mini", 7000, 500, 6000) == Decimal("0.001800")
