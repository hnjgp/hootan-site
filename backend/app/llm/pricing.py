"""Official model prices and the cost of one call computed from real token counts."""

from decimal import Decimal

# USD per 1M tokens: (input, output). Reasoning tokens are billed as output.
PRICES: dict[str, tuple[Decimal, Decimal]] = {
    "gemini-2.5-flash": (Decimal("0.30"), Decimal("2.50")),
    "gemini-2.5-flash-lite": (Decimal("0.10"), Decimal("0.40")),
    "gpt-4.1-mini": (Decimal("0.40"), Decimal("1.60")),
    "gpt-4.1-nano": (Decimal("0.10"), Decimal("0.40")),
    "gpt-5-nano": (Decimal("0.05"), Decimal("0.40")),
    "text-embedding-3-small": (Decimal("0.02"), Decimal(0)),
}

MILLION = Decimal(1_000_000)


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> Decimal:
    """Cost of one call in USD, rounded to 6 decimals like the llm_usage column."""
    price_in, price_out = PRICES[model]
    cost = (tokens_in * price_in + tokens_out * price_out) / MILLION
    return cost.quantize(Decimal("0.000001"))
