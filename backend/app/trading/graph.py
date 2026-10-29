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

from app.db.models import PortfolioTrade, SessionEvent, TradingSession
from app.llm.client import LLMClient
from app.trading import prompts
from app.trading.portfolio import Portfolio
from app.trading.risk import Order, apply_pm, check_proposal
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
    portfolio: Portfolio
    briefing: str
    transcript: Annotated[list[str], operator.add]
    proposal: TraderProposal | None
    order: Order


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


def describe(order: Order) -> str:
    """The order in one short phrase, e.g. 'BUY 0.25 BTC'."""
    return order.action if order.action == "HOLD" else f"{order.action} {order.qty} BTC"


def code_check(order: Order) -> str:
    """What the risk code did, stated plainly.

    With only 'Notes: none', the risk manager and PM claimed the size had been cut
    when it had not (first real meeting, 2026-10-27).
    """
    if order.notes:
        text = f"Code check changed the proposal: {' '.join(order.notes)}"
    else:
        text = "Code check: the proposal passed every rule unchanged."
    return f"{text} Checked order: {describe(order)}."


async def data(state: State, runtime: Runtime[Meeting]) -> State:
    line = prompts.market_line(state["market"])
    briefing = f"{line}\n{prompts.portfolio_line(state['portfolio'], state['price'])}"
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
        text, payload = "I could not form a valid proposal, so I propose HOLD.", None
    else:
        text = f"{proposal.reason} Proposal: {proposal.action} {proposal.size_pct:g}%."
        payload = proposal.model_dump()
    lines = await record(runtime.context, "trader", "decision", text, payload=payload)
    return {"proposal": proposal, "transcript": lines}


async def risk(state: State, runtime: Runtime[Meeting]) -> State:
    order = check_proposal(state["proposal"], state["portfolio"], state["price"])
    text = await speak(runtime.context, "risk", state, extra=code_check(order))
    payload = {"action": order.action, "qty": str(order.qty), "notes": order.notes}
    lines = await record(runtime.context, "risk", "risk", text, payload=payload)
    return {"order": order, "transcript": lines}


async def pm(state: State, runtime: Runtime[Meeting]) -> State:
    m, order, price = runtime.context, state["order"], state["price"]
    decision = None
    if order.action != "HOLD":
        decision = await decide(m, "pm", state, PMDecision, extra=code_check(order))
    final = apply_pm(order, decision, price)
    text = decision.reason if decision else "Nothing to trade today; we hold."
    text += f" Final decision: {describe(final)}"
    if final.stop_price:
        text += f", stop loss at {final.stop_price}"
    text += "."
    payload = {
        "action": final.action,
        "qty": str(final.qty),
        "stop_price": str(final.stop_price) if final.stop_price else None,
        "notes": final.notes,
    }
    lines = await record(m, "pm", "decision", text, payload=payload)
    return {"order": final, "transcript": lines}


async def execute(state: State, runtime: Runtime[Meeting]) -> State:
    """Apply the final order to the virtual portfolio and the session row."""
    m, order, price = runtime.context, state["order"], state["price"]
    if order.action != "HOLD":
        m.db.add(
            PortfolioTrade(
                session_id=m.row.id,
                side=order.action,
                qty=order.qty,
                price=price,
                stop_price=order.stop_price,
                reason="Daily meeting decision",
            )
        )
    m.row.decision, m.row.price = order.action, price
    m.row.qty = None if order.action == "HOLD" else order.qty
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
    portfolio: Portfolio,
) -> Order:
    """Hold the meeting for `row` and return the final order.

    `market` holds plain floats (stored as JSON); trades use the exact Decimal price.
    """
    state = {
        "market": market,
        "price": Decimal(str(market["price"])),
        "portfolio": portfolio,
        "transcript": [],
    }
    result = await GRAPH.ainvoke(state, context=Meeting(db, llm, row))
    return result["order"]
