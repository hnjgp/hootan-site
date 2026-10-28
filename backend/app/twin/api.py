"""Twin chat over Server-Sent Events, and the lead form for questions it cannot answer."""

from collections.abc import AsyncIterator
from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ChatLog, Lead
from app.db.session import get_session
from app.llm.budget import BudgetExceeded
from app.llm.client import Completion, LLMClient, get_llm_client
from app.security.rate_limit import RateLimiter, limit_by_ip
from app.security.visitor import visitor_id
from app.twin.chunking import detect_lang
from app.twin.prompt import HANDOFF, build_messages, filter_output, is_handoff
from app.twin.retrieval import Hit, search

router = APIRouter(prefix="/api")

# Nearest chunk farther than this, and no rare shared word, means the knowledge has
# no answer (Decision Log).
HANDOFF_DISTANCE = 0.80
MAX_TOKENS = 400

HANDOFF_TEXT = {
    "fa": "جواب این سؤال را در منابعم پیدا نکردم. اگر ایمیلتان را بگذارید، "
    "سؤال را برای خود هوتن می‌فرستم تا جوابتان را بدهد.",
    "en": "I couldn't find the answer to this in my sources. If you leave your "
    "email, I'll pass your question to Hootan and he'll get back to you.",
}
FALLBACK_TEXT = {
    "fa": "دستیار هوش مصنوعی موقتاً خاموش است. رزومه را ببینید یا به {email} ایمیل بزنید.",
    "en": "The AI assistant is temporarily off. Please see the resume or email {email}.",
}

CHAT_LIMITER = RateLimiter(10, timedelta(days=1))
CHAT_LIMITERS = (CHAT_LIMITER,)
LEAD_LIMITERS = (RateLimiter(5, timedelta(days=1)),)
chat_limits = limit_by_ip(*CHAT_LIMITERS)
lead_limits = limit_by_ip(*LEAD_LIMITERS)


class Turn(BaseModel):
    """One earlier message of the conversation, sent back by the browser."""

    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[Turn] = Field(default=[], max_length=6)


class LeadRequest(BaseModel):
    email: EmailStr
    question: str = Field(min_length=1, max_length=500)


SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClientDep = Annotated[LLMClient, Depends(get_llm_client)]


def event(name: str, data) -> ServerSentEvent:
    return ServerSentEvent(event=name, data=data)


def clean(text: str) -> str:
    """Filter secrets and drop any stray handoff marker from visible text."""
    return filter_output(text).replace(HANDOFF, "")


def source_list(hits: list[Hit]) -> list[dict]:
    """Unique source files in rank order, for the sources event and the log."""
    seen: dict[str, str] = {}
    for hit in hits:
        seen.setdefault(hit.source, hit.title)
    return [{"file": f, "title": t} for f, t in seen.items()]


async def answer(
    question: str,
    history: list[dict],
    session: AsyncSession,
    client: LLMClient,
    log: ChatLog,
) -> AsyncIterator[ServerSentEvent]:
    """Search, then either hand off or stream the model's answer; fills in the log."""
    settings = client.settings
    yield event("status", {"state": "thinking", "step": "searching"})
    hits = await search(session, client, question, lang=detect_lang(question))
    sources = source_list(hits)
    for s in sources:
        yield event("status", {"state": "thinking", "step": f"searching: {s['file']}"})

    far = all(h.distance > HANDOFF_DISTANCE and not h.rare_word for h in hits)
    handoff = not hits or far
    if not handoff:
        yield event("status", {"state": "answering"})
        messages = build_messages(question, hits, history)
        buffer, decided = "", False
        async for item in client.stream_chat(
            session, "twin", settings.model_twin, messages, MAX_TOKENS
        ):
            if isinstance(item, Completion):
                log.model, log.cost_usd = settings.model_twin, item.cost_usd
                log.tokens_in, log.tokens_out = item.tokens_in, item.tokens_out
                log.answer = filter_output(item.text)
            elif decided:
                if not handoff:
                    yield event("token", {"text": clean(item)})
            else:
                # Hold back the start until we know it is not the handoff marker.
                buffer += item
                if len(buffer) >= len(HANDOFF):
                    decided, handoff = True, is_handoff(buffer)
                    if not handoff:
                        yield event("token", {"text": clean(buffer)})
        if not decided:
            handoff = is_handoff(buffer) or not buffer.strip()
            if not handoff:
                yield event("token", {"text": clean(buffer)})

    lang = detect_lang(question)
    if handoff:
        log.answer = HANDOFF_TEXT[lang]
        yield event("handoff", {"message": HANDOFF_TEXT[lang]})
    else:
        log.sources = sources
        yield event("sources", sources)


@router.post(
    "/twin/chat",
    response_class=EventSourceResponse,
    dependencies=[Depends(chat_limits)],
)
async def twin_chat(
    body: ChatRequest,
    request: Request,
    session: SessionDep,
    client: ClientDep,
) -> AsyncIterator[ServerSentEvent]:
    """Events: status, token, sources or handoff, fallback when AI is off, then done.

    The done event carries how many questions the visitor has left today.
    """
    log = ChatLog(
        visitor_id=visitor_id(request, client.settings), question=body.question
    )
    history = [t.model_dump() for t in body.history]
    try:
        async for e in answer(body.question, history, session, client, log):
            yield e
    except BudgetExceeded:
        email = client.settings.contact_email
        log.answer = FALLBACK_TEXT[detect_lang(body.question)].format(email=email)
        yield event("fallback", {"message": log.answer})
    session.add(log)
    await session.commit()
    yield event("done", {"left": CHAT_LIMITER.remaining(request.client.host)})


@router.post("/leads", status_code=201, dependencies=[Depends(lead_limits)])
async def create_lead(body: LeadRequest, session: SessionDep) -> dict:
    """Store a visitor's email with the question the twin could not answer."""
    session.add(Lead(email=body.email, context=body.question))
    await session.commit()
    return {"ok": True}
