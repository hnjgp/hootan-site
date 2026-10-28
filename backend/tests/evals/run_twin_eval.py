"""Ask the real twin every case in twin_cases.json, score it and write RESULTS.md.

Run from backend/ after ingest: uv run python -m tests.evals.run_twin_eval
It uses the same code path as the chat endpoint, with real embeddings and model calls.
"""

import asyncio
import json
import re
from pathlib import Path

from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import ChatLog, LLMUsage
from app.db.session import SessionLocal
from app.llm.client import LLMClient
from app.twin.api import answer
from app.twin.prompt import HANDOFF

HERE = Path(__file__).parent
CASES = json.loads((HERE / "twin_cases.json").read_text("utf-8"))
COURSE_WORDS = re.compile(
    r"\bcourse|\bclass(?!ifi)|exercise|دوره|کلاس(?!یفیکیشن)|تمرین|آموزشی",
    re.IGNORECASE,
)
ALWAYS_FORBIDDEN = re.compile(r"claude|chatgpt|copilot|هوتان", re.IGNORECASE)


def score(case: dict, text: str, handed_off: bool) -> list[str]:
    """Return the reasons a case failed; an empty list means it passed."""
    problems = []
    if case["expect"] == "handoff" and not handed_off:
        problems.append("expected handoff")
    if case["expect"] == "answer" and handed_off:
        problems.append("unexpected handoff")
    low = text.lower()
    for options in case.get("facts", []):
        if not handed_off and not any(o.lower() in low for o in options):
            problems.append(f"missing {options}")
    problems += [f"wrong '{w}'" for w in case.get("wrong", []) if w.lower() in low]
    if not case.get("allow_course") and COURSE_WORDS.search(text):
        problems.append(f"course word '{COURSE_WORDS.search(text).group()}'")
    if ALWAYS_FORBIDDEN.search(text) or HANDOFF in text:
        problems.append("forbidden word")
    return problems


async def ask(session, client, question: str) -> tuple[str, bool]:
    """Run one question through the twin; return the visible text and handoff flag."""
    log = ChatLog(visitor_id="eval", question=question)
    text, handed_off = "", False
    async for e in answer(question, [], session, client, log):
        if e.event == "token":
            text += e.data["text"]
        elif e.event == "handoff":
            handed_off = True
    return text, handed_off


async def main() -> None:
    """Run all cases, print a summary and write RESULTS.md."""
    client = LLMClient(get_settings())
    rows, passed = [], {"answer": [0, 0], "handoff": [0, 0], "any": [0, 0]}
    async with SessionLocal() as session:
        start = await session.scalar(select(func.max(LLMUsage.id))) or 0
        for case in CASES:
            text, handed_off = await ask(session, client, case["q"])
            problems = score(case, text, handed_off)
            passed[case["expect"]][0] += not problems
            passed[case["expect"]][1] += 1
            mark = "PASS" if not problems else "FAIL " + "; ".join(problems)
            print(f"{mark:40.40} {case['q']}")
            shown = "(handoff)" if handed_off else text.replace("\n", " ")
            rows.append(f"| {case['q']} | {case['expect']} | {mark} | {shown} |")
        cost = await session.scalar(
            select(func.sum(LLMUsage.cost_usd)).where(LLMUsage.id > start)
        )

    total = sum(p for p, _ in passed.values()), sum(n for _, n in passed.values())
    summary = [
        f"- Answered correctly: {passed['answer'][0]}/{passed['answer'][1]}",
        f"- Handed off when they should: {passed['handoff'][0]}/{passed['handoff'][1]}",
        f"- Salary handled without numbers: {passed['any'][0]}/{passed['any'][1]}",
        f"- Total: {total[0]}/{total[1]} ({100 * total[0] // total[1]}%)",
        f"- Cost of this run: ${cost}",
    ]
    print("\n".join(summary))
    report = [
        "# Digital twin eval results",
        "",
        f"Model: {client.settings.model_twin}. Cases: `twin_cases.json`.",
        "",
        *summary,
        "",
        "| Question | Expected | Result | Answer |",
        "|---|---|---|---|",
        *rows,
    ]
    (HERE / "RESULTS.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
