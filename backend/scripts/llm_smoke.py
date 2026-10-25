"""Smoke test for the LLM provider: models, one call, one streamed call, embeddings.

Run from backend/: uv run python -m scripts.llm_smoke
"""

import math

from openai import OpenAI

from app.config import get_settings


def cosine(a: list[float], b: list[float]) -> float:
    """Cosine similarity of two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def check_stream(client: OpenAI, model: str) -> None:
    """Stream a short Persian answer and show whether the last chunk reports usage."""
    stream = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "در دو جمله بگو RAG چیست."}],
        max_completion_tokens=400,
        stream=True,
        stream_options={"include_usage": True},
    )
    chunks, text, usage = 0, "", None
    for chunk in stream:
        chunks += 1
        if chunk.choices and chunk.choices[0].delta.content:
            text += chunk.choices[0].delta.content
        if chunk.usage:
            usage = chunk.usage
    print(f"stream chunks: {chunks}")
    print("stream text:", text)
    print("stream usage:", usage)


def check_embeddings(client: OpenAI, model: str) -> None:
    """Embed an English text, its Persian translation and an unrelated text."""
    texts = [
        "Hootan built an AI agent platform with LangGraph.",
        "هوتن یک پلتفرم ایجنت هوش مصنوعی با LangGraph ساخت.",
        "The weather in Tehran is sunny today.",
    ]
    response = client.embeddings.create(model=model, input=texts)
    vectors = [d.embedding for d in response.data]
    print(f"embedding dims: {len(vectors[0])}")
    print("embedding usage:", response.usage)
    print(f"similarity en-fa same meaning: {cosine(vectors[0], vectors[1]):.3f}")
    print(f"similarity en-unrelated: {cosine(vectors[0], vectors[2]):.3f}")


def main() -> None:
    """Run every check against the configured provider."""
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

    check_stream(client, settings.model_twin)
    check_embeddings(client, settings.model_embed)


if __name__ == "__main__":
    main()
