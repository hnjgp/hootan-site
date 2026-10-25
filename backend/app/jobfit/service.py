"""Run one job fit check: profile and ad to the model, then the rubric caps in code."""

from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.jobfit.prompt import build_messages, load_profile
from app.jobfit.schema import FitResult
from app.llm.budget import TEHRAN
from app.llm.client import Completion, LLMClient

MAX_TOKENS = 800
# Rubric bands (Hootan's choice): every must-have skill met -> at least 90;
# one missing -> at most 89; two or more missing -> at most 69.
FLOOR_ALL_MET = 90
CAP_ONE_MISSING = 89
CAP_MORE_MISSING = 69


def apply_bands(result: FitResult) -> FitResult:
    """Move the score into the band set by the must-have skills.

    Experience requirements (years, seniority, degrees) are shown as gaps but never
    move the score. The model ignored these bands when they were only in the prompt
    (real tests, 2026-10-26), so they are enforced here like the trading risk rules.
    """
    skills = [r for r in result.requirements if r.must_have and r.kind == "skill"]
    missing = sum(r.status == "missing" for r in skills)
    if skills and all(r.status == "met" for r in skills):
        result.score = max(result.score, FLOOR_ALL_MET)
    elif missing == 1:
        result.score = min(result.score, CAP_ONE_MISSING)
    elif missing > 1:
        result.score = min(result.score, CAP_MORE_MISSING)
    return result


async def check_fit(
    session: AsyncSession, client: LLMClient, job_ad: str, lang: str
) -> tuple[FitResult, Completion]:
    """Score Hootan's fit for a job ad; raises BudgetExceeded if a cap is used up."""
    profile = await load_profile(session)
    today = datetime.now(TEHRAN).date()
    messages = build_messages(profile, job_ad, lang, today)
    model = client.settings.model_jobfit
    result, completion = await client.structured(
        session, "jobfit", model, messages, MAX_TOKENS, FitResult
    )
    return apply_bands(result), completion
