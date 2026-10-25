"""Run every ad in jobfit_cases.json twice through the real model and write
JOBFIT_RESULTS.md.

Run from backend/ after ingest: uv run python -m tests.evals.run_jobfit_eval
It uses check_fit, the same code path as POST /api/jobfit.
"""

import asyncio
import json
import re
from pathlib import Path

from sqlalchemy import func, select

from app.config import get_settings
from app.db.models import LLMUsage
from app.db.session import SessionLocal
from app.jobfit.schema import FitResult
from app.jobfit.service import MAX_TOKENS, check_fit
from app.llm.client import LLMClient
from app.twin.chunking import detect_lang

HERE = Path(__file__).parent
CASES = json.loads((HERE / "jobfit_cases.json").read_text("utf-8"))
RUNS = 2
MAX_SPREAD = 10
FORBIDDEN = re.compile(
    r"\bextensive|\bexpert\b|in the future|claude|chatgpt|هوتان", re.IGNORECASE
)


def visible_items(result: FitResult) -> list[str]:
    """Every text item a visitor sees (requirements are internal)."""
    items = [result.summary, *result.gaps, *result.questions]
    return items + [f"{s.point} {s.evidence}" for s in result.strengths]


def visible_text(result: FitResult) -> str:
    return "\n".join(visible_items(result))


def check(case: dict, results: list[FitResult]) -> list[str]:
    """Return the reasons a case failed; an empty list means it passed."""
    problems = []
    scores = [r.score for r in results]
    if not all(case["min"] <= s <= case["max"] for s in scores):
        problems.append(f"score {scores} not in {case['min']}-{case['max']}")
    if max(scores) - min(scores) > MAX_SPREAD:
        problems.append(f"spread {max(scores) - min(scores)}")
    for r in results:
        if len(r.questions) != case.get("questions", 3):
            problems.append(f"{len(r.questions)} questions")
        if case["lang"] == "fa":
            problems += [
                f"not Persian: '{t[:40]}'"
                for t in visible_items(r)
                if detect_lang(t) != "fa"
            ]
        text = visible_text(r)
        if match := FORBIDDEN.search(text):
            around = text[max(match.start() - 30, 0) : match.end() + 20]
            problems.append(f"forbidden in '{around}'".replace("\n", " "))
    return problems


async def main() -> None:
    """Run all cases, print a summary and write JOBFIT_RESULTS.md."""
    client = LLMClient(get_settings())
    rows, passed, max_out = [], 0, 0
    async with SessionLocal() as session:
        start = await session.scalar(select(func.max(LLMUsage.id))) or 0
        for case in CASES:
            results = []
            for _ in range(RUNS):
                result, completion = await check_fit(
                    session, client, case["ad"], case["lang"]
                )
                results.append(result)
                max_out = max(max_out, completion.tokens_out)
            problems = check(case, results)
            passed += not problems
            mark = "PASS" if not problems else "FAIL " + "; ".join(problems)
            scores = " / ".join(str(r.score) for r in results)
            print(f"{scores:>8}  {case['name']}: {mark}")
            first = results[0]
            gaps = "<br>".join(first.gaps)
            rows.append(
                f"| {case['name']} | {case['min']}-{case['max']} | {scores} | "
                f"{mark} | {first.summary} | {gaps} |"
            )
        cost = await session.scalar(
            select(func.sum(LLMUsage.cost_usd)).where(LLMUsage.id > start)
        )

    summary = [
        f"- Passed: {passed}/{len(CASES)} ({100 * passed // len(CASES)}%)",
        f"- Each ad ran {RUNS} times; allowed spread {MAX_SPREAD} points.",
        f"- Cost of this run (as we record it): ${cost}",
        f"- Most output tokens in one reply: {max_out} (limit {MAX_TOKENS})",
    ]
    print("\n".join(summary))
    report = [
        "# Job fit eval results",
        "",
        f"Model: {client.settings.model_jobfit}. Cases: `jobfit_cases.json`.",
        "",
        *summary,
        "",
        "| Ad | Expected | Scores | Result | Summary (run 1) | Gaps (run 1) |",
        "|---|---|---|---|---|---|",
        *rows,
    ]
    (HERE / "JOBFIT_RESULTS.md").write_text("\n".join(report) + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
