"""Fake LLM client for tests: canned replies, no network, same budget and recording."""

from app.config import Settings
from app.llm.client import Completion, LLMClient


class FakeLLMClient(LLMClient):
    """Returns the given replies in order and remembers the messages it received."""

    def __init__(self, settings: Settings, replies: list[str]):
        self.settings = settings
        self.replies = list(replies)
        self.calls: list[list[dict]] = []

    async def _complete(
        self, model: str, messages: list[dict], max_tokens: int
    ) -> Completion:
        """Pop the next canned reply with fixed token counts (100 in, 50 out)."""
        self.calls.append(messages)
        return Completion(text=self.replies.pop(0), tokens_in=100, tokens_out=50)
