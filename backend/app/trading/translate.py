"""Persian text of a finished meeting: one call translates every event at once.

Translation is optional: if it fails, text_fa stays empty and the site shows English.
gpt-5-nano returned the English unchanged in one of two real calls, with the right
count (probe, 2026-10-27), so every text must contain Persian letters.
"""

import json

from openai import APIError
from pydantic import BaseModel, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SessionEvent
from app.llm.budget import BudgetExceeded
from app.llm.client import LLMClient

# Persian needs more tokens than English; a meeting is about 7 short texts.
MAX_TOKENS = 2000
SYSTEM = (
    "You translate the transcript of an AI trading team's meeting into fluent, "
    "natural Persian (Farsi) for a general audience. Translate each text in the "
    "JSON list on its own and return exactly one translation per text, in the same "
    "order. Keep numbers exactly as written. Keep BTC, USDT and RSI in Latin letters."
)


def is_persian(text: str) -> bool:
    """True when the text has at least one Arabic-script (Persian) letter."""
    return any("؀" <= c <= "ۿ" for c in text)


class Translation(BaseModel):
    """Persian texts, one per input text, in the same order."""

    texts: list[str]


async def translate_session(db: AsyncSession, llm: LLMClient, session_id: int) -> bool:
    """Fill text_fa of every event of the session; return False if it was skipped."""
    events = list(
        await db.scalars(
            select(SessionEvent)
            .where(SessionEvent.session_id == session_id)
            .order_by(SessionEvent.seq)
        )
    )
    messages = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": json.dumps([e.text_en for e in events])},
    ]
    model = llm.settings.model_translate
    try:
        reply, _ = await llm.structured(
            db, "trading", model, messages, MAX_TOKENS, Translation, temperature=0
        )
    except (ValidationError, BudgetExceeded, APIError):
        return False
    if len(reply.texts) != len(events) or not all(map(is_persian, reply.texts)):
        return False
    for event, text in zip(events, reply.texts):
        event.text_fa = text
    await db.commit()
    return True
