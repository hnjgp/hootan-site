"""Smoke test for the LLM provider: list models and make one tiny real call.

Run from backend/: uv run python -m scripts.llm_smoke
"""

from openai import OpenAI

from app.config import get_settings


def main() -> None:
    """Print available embedding models and the token usage of one short call."""
    settings = get_settings()
    client = OpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

    ids = sorted(m.id for m in client.models.list())
    print(f"models available: {len(ids)}")
    print("embedding models:", [i for i in ids if "embed" in i])
    for name in (settings.model_twin, settings.model_trading):
        print(f"{name} available: {name in ids}")

    response = client.chat.completions.create(
        model=settings.model_trading,
        messages=[{"role": "user", "content": "Reply with one word: hello"}],
        max_completion_tokens=500,
    )
    print("reply:", response.choices[0].message.content)
    print("usage:", response.usage)


if __name__ == "__main__":
    main()
