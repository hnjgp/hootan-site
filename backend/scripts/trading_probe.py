"""Probe: does gpt-5-nano return a complete TraderProposal under the 250-token cap?

Run from backend/: uv run python -m scripts.trading_probe
"""

import asyncio

from pydantic import ValidationError

from app.config import get_settings
from app.db.session import SessionLocal
from app.llm.client import LLMClient
from app.trading.schema import TraderProposal

MAX_TOKENS = 250
MESSAGES = [
    {
        "role": "system",
        "content": "You are the trader of a small AI trading team that trades BTC/USDT "
        "with virtual money. Read the meeting and propose one action. Keep the reason "
        "to two short sentences.",
    },
    {
        "role": "user",
        "content": "Market: price 79736, 24h high 80900, 24h low 78850, RSI(14) 39.4, "
        "7-day average 81074, 30-day average 82736.\n"
        "Portfolio: cash 10000 USD, BTC 0.\n"
        "Bull: RSI is near oversold and the price sits at the bottom of its range; "
        "a small entry has good risk/reward.\n"
        "Bear: price is below both averages, so the trend is down; wait for strength.",
    },
]


async def main() -> None:
    """Make three real calls and print each reply, its token counts and cost."""
    client = LLMClient(get_settings())
    model = client.settings.model_trading
    async with SessionLocal() as session:
        for i in range(3):
            try:
                proposal, done = await client.structured(
                    session, "trading", model, MESSAGES, MAX_TOKENS, TraderProposal
                )
                print(f"{i + 1}: {proposal}")
            except ValidationError as e:
                print(f"{i + 1}: invalid reply: {e.errors()[0]['msg']}")
                continue
            print(f"   tokens {done.tokens_in}/{done.tokens_out}, cost {done.cost_usd}")


if __name__ == "__main__":
    asyncio.run(main())
