"""LLM client: budget check, then the call (timeout and retries), then cost recording."""

from dataclasses import dataclass

from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.db.models import LLMUsage
from app.llm.budget import check_budget
from app.llm.pricing import cost_usd


@dataclass
class Completion:
    """Text of one reply and the real token counts reported by the provider."""

    text: str
    tokens_in: int
    tokens_out: int


class LLMClient:
    """OpenAI-compatible client; the provider is chosen by LLM_BASE_URL and LLM_API_KEY."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
            timeout=30,
            max_retries=2,
        )

    async def chat(
        self,
        session: AsyncSession,
        feature: str,
        model: str,
        messages: list[dict],
        max_tokens: int,
    ) -> str:
        """Return the reply text; raise BudgetExceeded before calling if a cap is used up.

        Usage is committed right away so it counts even if the request fails later.
        """
        await check_budget(session, feature, self.settings)
        result = await self._complete(model, messages, max_tokens)
        session.add(
            LLMUsage(
                feature=feature,
                model=model,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                cost_usd=cost_usd(model, result.tokens_in, result.tokens_out),
            )
        )
        await session.commit()
        return result.text

    async def _complete(
        self, model: str, messages: list[dict], max_tokens: int
    ) -> Completion:
        """One chat completion; reasoning tokens count toward max_tokens and output."""
        response = await self.api.chat.completions.create(
            model=model, messages=messages, max_completion_tokens=max_tokens
        )
        return Completion(
            text=response.choices[0].message.content or "",
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
        )
