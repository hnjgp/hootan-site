"""Fake LLM client for tests: canned replies, no network, same budget and recording."""

import hashlib
import random
from collections.abc import AsyncIterator

from app.config import Settings
from app.db.models import EMBED_DIM
from app.llm.client import Completion, LLMClient


def fake_vector(text: str) -> list[float]:
    """Deterministic vector for a text: equal texts get equal vectors."""
    seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:8])
    rng = random.Random(seed)
    return [rng.gauss(0, 1) for _ in range(EMBED_DIM)]


class FakeLLMClient(LLMClient):
    """Returns the given replies in order and remembers the messages it received."""

    def __init__(self, settings: Settings, replies: list[str] = ()):
        self.settings = settings
        self.replies = list(replies)
        self.calls: list[list[dict]] = []
        self.embedded: list[str] = []

    async def _complete(
        self,
        model: str,
        messages: list[dict],
        max_tokens: int,
        response_format: dict | None = None,
    ) -> Completion:
        """Pop the next canned reply with fixed token counts (100 in, 50 out)."""
        self.calls.append(messages)
        return Completion(text=self.replies.pop(0), tokens_in=100, tokens_out=50)

    async def _stream(
        self, model: str, messages: list[dict], max_tokens: int
    ) -> AsyncIterator[str | Completion]:
        """Yield the next canned reply word by word, then its Completion."""
        result = await self._complete(model, messages, max_tokens)
        words = result.text.split(" ")
        yield words[0]
        for word in words[1:]:
            yield " " + word
        yield result

    async def _embed(
        self, model: str, texts: list[str]
    ) -> tuple[list[list[float]], int]:
        """Fake vectors with 10 input tokens per text."""
        self.embedded.extend(texts)
        return [fake_vector(t) for t in texts], 10 * len(texts)
