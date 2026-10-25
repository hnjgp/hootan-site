"""LLM client: budget check, then the call (timeout and retries), then cost recording."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from decimal import Decimal

from openai import AsyncOpenAI
from openai.lib._pydantic import to_strict_json_schema
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.models import LLMUsage
from app.llm.budget import check_budget
from app.llm.pricing import cost_usd

# Thinking tokens count toward max_tokens; with default effort they used the whole
# trading cap and the reply came back empty (real-call probe, 2026-10-25).
REASONING_EFFORT = {"gpt-5-nano": "minimal"}


@dataclass
class Completion:
    """Text of one reply and the real token counts reported by the provider."""

    text: str
    tokens_in: int
    tokens_out: int
    cost_usd: Decimal | None = None


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
        await self._record(session, feature, model, result)
        return result.text

    async def structured[T: BaseModel](
        self,
        session: AsyncSession,
        feature: str,
        model: str,
        messages: list[dict],
        max_tokens: int,
        schema: type[T],
        temperature: float | None = None,
    ) -> tuple[T, Completion]:
        """Return the reply parsed into `schema` and its Completion.

        The provider enforces the JSON schema (strict mode). Usage is recorded before
        validation, so a bad reply still counts toward the budget. Through AvalAI,
        Gemini ignored the schema while OpenAI models followed it (probe, 2026-10-26).
        Reasoning models (gpt-5 family) reject temperature, so it is optional.
        """
        await check_budget(session, feature, self.settings)
        extra = {
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": to_strict_json_schema(schema),
                    "strict": True,
                },
            }
        }
        if temperature is not None:
            extra["temperature"] = temperature
        result = await self._complete(model, messages, max_tokens, **extra)
        await self._record(session, feature, model, result)
        return schema.model_validate_json(result.text), result

    async def stream_chat(
        self,
        session: AsyncSession,
        feature: str,
        model: str,
        messages: list[dict],
        max_tokens: int,
    ) -> AsyncIterator[str | Completion]:
        """Yield text pieces as they arrive, then one Completion with the full text.

        The budget is checked before the call; usage is recorded when the stream ends,
        so the caller must read the stream to the end.
        """
        await check_budget(session, feature, self.settings)
        async for item in self._stream(model, messages, max_tokens):
            if isinstance(item, Completion):
                await self._record(session, feature, model, item)
            yield item

    async def embed(self, session: AsyncSession, texts: list[str]) -> list[list[float]]:
        """Return one embedding per text, checked and recorded as the embedding feature."""
        await check_budget(session, "embedding", self.settings)
        model = self.settings.model_embed
        vectors, tokens_in = await self._embed(model, texts)
        await self._record(session, "embedding", model, Completion("", tokens_in, 0))
        return vectors

    async def _record(
        self, session: AsyncSession, feature: str, model: str, result: Completion
    ) -> None:
        """Store the cost of one call in llm_usage and on the result, then commit."""
        result.cost_usd = cost_usd(model, result.tokens_in, result.tokens_out)
        session.add(
            LLMUsage(
                feature=feature,
                model=model,
                tokens_in=result.tokens_in,
                tokens_out=result.tokens_out,
                cost_usd=result.cost_usd,
            )
        )
        await session.commit()

    def _effort(self, model: str) -> dict:
        """Extra request arguments for the model's reasoning effort, if one is set."""
        if model in REASONING_EFFORT:
            return {"reasoning_effort": REASONING_EFFORT[model]}
        return {}

    async def _complete(
        self, model: str, messages: list[dict], max_tokens: int, **extra
    ) -> Completion:
        """One chat completion with the model's reasoning effort, if one is set;
        `extra` goes to the API as is (response_format, temperature)."""
        response = await self.api.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=max_tokens,
            **self._effort(model),
            **extra,
        )
        return Completion(
            text=response.choices[0].message.content or "",
            tokens_in=response.usage.prompt_tokens,
            tokens_out=response.usage.completion_tokens,
        )

    async def _stream(
        self, model: str, messages: list[dict], max_tokens: int
    ) -> AsyncIterator[str | Completion]:
        """Stream one chat completion; the last chunk carries the usage (AvalAI probe)."""
        stream = await self.api.chat.completions.create(
            model=model,
            messages=messages,
            max_completion_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
            **self._effort(model),
        )
        text, usage = "", None
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                piece = chunk.choices[0].delta.content
                text += piece
                yield piece
            if chunk.usage:
                usage = chunk.usage
        yield Completion(text, usage.prompt_tokens, usage.completion_tokens)

    async def _embed(
        self, model: str, texts: list[str]
    ) -> tuple[list[list[float]], int]:
        """Embed a batch of texts; return the vectors and the input token count."""
        response = await self.api.embeddings.create(model=model, input=texts)
        return [d.embedding for d in response.data], response.usage.prompt_tokens


def get_llm_client() -> LLMClient:
    """FastAPI dependency for the real client; tests override it with the fake."""
    return LLMClient(get_settings())
