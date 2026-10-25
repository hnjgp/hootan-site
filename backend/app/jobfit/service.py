"""Run one job fit check: profile and ad to the model, then the rubric bands in code."""

from datetime import datetime
from fractions import Fraction

from sqlalchemy.ext.asyncio import AsyncSession

from app.jobfit.prompt import build_messages, load_profile
from app.jobfit.schema import FitResult
from app.llm.budget import TEHRAN
from app.llm.client import Completion, LLMClient

# 800 cut Persian replies mid-JSON (eval, 2026-10-26); see the eval for real usage.
MAX_TOKENS = 1500
# Scoring must repeat: at the default temperature one ad scored 55 and then 70.
TEMPERATURE = 0
CREDIT = {"met": 1, "partial": Fraction(1, 2), "missing": 0}


def band(share: Fraction) -> tuple[int, int]:
    """Score range for the share of must-have skills met (Hootan's bands)."""
    if share == 1:
        return 90, 100
    if share >= Fraction(2, 3):
        return 70, 89
    if share > 0:
        return 50, 69
    return 0, 49


def apply_bands(result: FitResult) -> FitResult:
    """Clamp the score into the band of the must-have skills it met.

    Met counts 1 and partial 1/2. Experience requirements (years, seniority,
    degrees) are shown as gaps but never move the score. The model ignored the
    bands when they were only in the prompt (real tests, 2026-10-26), so they are
    enforced here like the trading risk rules; the model picks the place inside.
    """
    skills = [r for r in result.requirements if r.must_have and r.kind == "skill"]
    if skills:
        share = sum(CREDIT[r.status] for r in skills) / Fraction(len(skills))
        low, high = band(share)
        result.score = min(max(result.score, low), high)
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
        session,
        "jobfit",
        model,
        messages,
        MAX_TOKENS,
        FitResult,
        temperature=TEMPERATURE,
    )
    return apply_bands(result), completion
