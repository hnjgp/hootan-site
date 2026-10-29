"""Persian text of each meeting line, translated as soon as the line is spoken.

The first visitor watches the meeting live, so every line needs its Persian before it
is saved. Earlier lines and their translations go along as context, so terms stay the
same through the meeting. Translation is optional: if it fails, text_fa stays empty
and the site shows English. gpt-5-nano returned the English unchanged in a real call
(probe, 2026-10-27), so the reply must contain Persian letters.
"""

from openai import APIError
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.budget import BudgetExceeded
from app.llm.client import LLMClient

MAX_TOKENS = 400
# A healthy reply takes under 3 seconds; a bad route (a VPN on the machine, probe
# 2026-10-29) can hang a call for 20 to 30 seconds, so it is dropped early and retried.
TIMEOUT = 10
SYSTEM = (
    "You translate lines of an AI trading team's meeting into fluent, natural "
    "Persian (Farsi) for a general audience, one line at a time, using the same "
    "terms as your earlier translations. Keep numbers exactly as written. "
    "Keep BTC, USDT and RSI in Latin letters."
)


def is_persian(text: str) -> bool:
    """True when the text has at least one Arabic-script (Persian) letter."""
    return any("؀" <= c <= "ۿ" for c in text)


class Translation(BaseModel):
    """The Persian text of one line."""

    text: str


async def translate_line(
    db: AsyncSession, llm: LLMClient, text: str, before: list[tuple[str, str]]
) -> str | None:
    """Persian of `text`, with earlier (English, Persian) pairs as context; None on failure."""
    messages = [{"role": "system", "content": SYSTEM}]
    for en, fa in before:
        messages += [
            {"role": "user", "content": en},
            {"role": "assistant", "content": Translation(text=fa).model_dump_json()},
        ]
    messages.append({"role": "user", "content": text})
    model = llm.settings.model_translate
    try:
        reply, _ = await llm.structured(
            db,
            "trading",
            model,
            messages,
            MAX_TOKENS,
            Translation,
            temperature=0,
            timeout=TIMEOUT,
        )
    except (ValidationError, BudgetExceeded, APIError):
        return None
    return reply.text if is_persian(reply.text) else None
