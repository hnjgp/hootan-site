"""The daily meeting as a LangGraph graph with a fixed order of seven speakers.

Each node saves its event right away, so the first visitor can watch live.
"""

import operator
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.runtime import Runtime
from pydantic import BaseModel, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SessionEvent, TradingSession
from app.exchange.book import Book, close_position, open_position
from app.llm.client import LLMClient
from app.trading import prompts
from app.trading.risk import Plan, apply_pm, check_proposal
from app.trading.schema import PMDecision, TraderProposal
from app.trading.translate import translate_line

MAX_TOKENS = 250
NAMES = {
    "data": "Data analyst",
    "news": "News analyst",
    "bull": "Bull",
    "bear": "Bear",
    "trader": "Trader",
    "risk": "Risk manager",
    "pm": "Portfolio manager",
}


@dataclass
class Meeting:
    """Run-scoped context: database, LLM client, the session row, the event counter
    and the (English, Persian) lines so far, which keep the translation consistent."""

    db: AsyncSession
    llm: LLMClient
    row: TradingSession
    seq: int = 0
    translated: list[tuple[str, str]] = field(default_factory=list)


class State(TypedDict, total=False):
    """What the meeting knows; the transcript grows as each speaker adds a line."""

    market: dict
    price: Decimal
    book: Book
    briefing: str
    transcript: Annotated[list[str], operator.add]
    proposal: TraderProposal | None
    plan: Plan


async def record(
    m: Meeting,
    agent: str,
    kind: str,
    text: str,
    payload: dict | None = None,
) -> list[str]:
    """Translate one event, save and commit it for live viewers; return its transcript line."""
    fa = await translate_line(m.db, m.llm, text, m.translated)
    if fa:
        m.translated.append((text, fa))
    m.seq += 1
    m.db.add(
        SessionEvent(
            session_id=m.row.id,
            seq=m.seq,
            agent=agent,
            kind=kind,
            text_en=text,
            text_fa=fa,
            payload=payload,
        )
    )
    await m.db.commit()
    return [f"{NAMES[agent]}: {text}"]


async def speak(m: Meeting, role: str, state: State, extra: str = "") -> str:
    """One free-text turn of an LLM speaker."""
    messages = prompts.messages(role, state["briefing"], state["transcript"], extra)
    model = m.llm.settings.model_trading
    return await m.llm.chat(m.db, "trading", model, messages, MAX_TOKENS)


async def decide[T: BaseModel](
    m: Meeting, role: str, state: State, schema: type[T], extra: str = ""
) -> T | None:
    """One structured turn; None when the reply does not fit the schema."""
    messages = prompts.messages(role, state["briefing"], state["transcript"], extra)
    model = m.llm.settings.model_trading
    try:
        reply, _ = await m.llm.structured(
            m.db, "trading", model, messages, MAX_TOKENS, schema
        )
    except ValidationError:
        return None
    return reply


def describe(plan: Plan) -> str:
    """The plan in one short phrase, e.g. 'close #3; open long 2x with 1,000.00 USD margin'."""
    parts = [f"close #{i}" for i in plan.close]
    if new := plan.new:
        text = (
            f"open {new.side} {new.leverage}x with {new.margin:,.2f} USD margin, "
            f"stop loss at {new.sl_price:,.2f}"
        )
        if new.tp_price:
            text += f", take profit at {new.tp_price:,.2f}"
        parts.append(text)
    return "; ".join(parts) or "no change"


def code_check(plan: Plan) -> str:
    """What the risk code did, stated plainly.

    With only 'Notes: none', the risk manager and PM claimed the size had been cut
    when it had not (first real meeting, 2026-10-27).
    """
    if plan.notes:
        text = f"Code check changed the proposal: {' '.join(plan.notes)}"
    else:
        text = "Code check: the proposal passed every rule unchanged."
    return f"{text} Checked plan: {describe(plan)}."


def plan_payload(plan: Plan) -> dict:
    """The plan as JSON for the event log."""
    new = plan.new
    return {
        "close": plan.close,
        "new": None
        if new is None
        else {
            "side": new.side,
            "margin": str(new.margin),
            "leverage": new.leverage,
            "tp_price": str(new.tp_price) if new.tp_price else None,
            "sl_price": str(new.sl_price),
        },
        "notes": plan.notes,
    }


async def data(state: State, runtime: Runtime[Meeting]) -> State:
    line = prompts.market_line(state["market"])
    briefing = f"{line}\n{prompts.book_line(state['book'], state['price'])}"
    lines = await record(
        runtime.context, "data", "speech", line, payload=state["market"]
    )
    return {"briefing": briefing, "transcript": lines}


async def news(state: State, runtime: Runtime[Meeting]) -> State:
    text = "No major news today; the team trades on price data alone."
    return {"transcript": await record(runtime.context, "news", "speech", text)}


async def bull(state: State, runtime: Runtime[Meeting]) -> State:
    text = await speak(runtime.context, "bull", state)
    return {"transcript": await record(runtime.context, "bull", "speech", text)}


async def bear(state: State, runtime: Runtime[Meeting]) -> State:
    text = await speak(runtime.context, "bear", state)
    return {"transcript": await record(runtime.context, "bear", "speech", text)}


async def trader(state: State, runtime: Runtime[Meeting]) -> State:
    proposal = await decide(runtime.context, "trader", state, TraderProposal)
    if proposal is None:
        text, payload = (
            "I could not form a valid proposal, so I propose no change.",
            None,
        )
    else:
        calls = ", ".join(f"{c.action} #{c.id}" for c in proposal.positions)
        new = proposal.new_position
        opening = (
            f"open {new.side} {new.leverage}x with {new.margin_pct:g}% margin"
            if new
            else "no new position"
        )
        text = f"{proposal.reason} Proposal: {calls or 'nothing open'}; {opening}."
        payload = proposal.model_dump()
    lines = await record(runtime.context, "trader", "decision", text, payload=payload)
    return {"proposal": proposal, "transcript": lines}


async def risk(state: State, runtime: Runtime[Meeting]) -> State:
    plan = check_proposal(state["proposal"], state["book"], state["price"])
    text = await speak(runtime.context, "risk", state, extra=code_check(plan))
    lines = await record(
        runtime.context, "risk", "risk", text, payload=plan_payload(plan)
    )
    return {"plan": plan, "transcript": lines}


async def pm(state: State, runtime: Runtime[Meeting]) -> State:
    m, plan = runtime.context, state["plan"]
    decision = None
    if not plan.empty:
        decision = await decide(m, "pm", state, PMDecision, extra=code_check(plan))
    final = apply_pm(plan, decision)
    text = decision.reason if decision else "Nothing to change today; we wait."
    text += f" Final decision: {describe(final)}."
    lines = await record(m, "pm", "decision", text, payload=plan_payload(final))
    return {"plan": final, "transcript": lines}


async def execute(state: State, runtime: Runtime[Meeting]) -> State:
    """Apply the final plan on the exchange and record it on the session row."""
    m, plan, price = runtime.context, state["plan"], state["price"]
    for position_id in plan.close:
        await close_position(m.db, None, position_id, price, "team")
    m.row.decision = "CLOSE" if plan.close else "HOLD"
    m.row.price, m.row.qty = price, None
    if new := plan.new:
        position = await open_position(
            m.db,
            None,
            new.side,
            new.margin,
            new.leverage,
            price,
            new.tp_price,
            new.sl_price,
            session_id=m.row.id,
        )
        m.row.decision, m.row.qty = new.side.upper(), position.qty
    await m.db.commit()
    return {}


def build_graph():
    """Fixed order: data, news, bull, bear, trader, risk, pm, then execute."""
    graph = StateGraph(State, context_schema=Meeting)
    order = [data, news, bull, bear, trader, risk, pm, execute]
    previous = START
    for node in order:
        graph.add_node(node.__name__, node)
        graph.add_edge(previous, node.__name__)
        previous = node.__name__
    graph.add_edge(previous, END)
    return graph.compile()


GRAPH = build_graph()


async def run_meeting(
    db: AsyncSession,
    llm: LLMClient,
    row: TradingSession,
    market: dict,
    book: Book,
) -> Plan:
    """Hold the meeting for `row` and return the final plan.

    `market` holds plain floats (stored as JSON); trades use the exact Decimal price.
    """
    state = {
        "market": market,
        "price": Decimal(str(market["price"])),
        "book": book,
        "transcript": [],
    }
    result = await GRAPH.ainvoke(state, context=Meeting(db, llm, row))
    return result["plan"]
