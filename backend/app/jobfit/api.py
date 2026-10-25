"""Job fit endpoint: a visitor pastes a job ad and gets a structured fit result."""

from datetime import timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import JobFitRequest
from app.db.session import get_session
from app.jobfit.schema import FitResult
from app.jobfit.service import check_fit
from app.llm.budget import BudgetExceeded
from app.llm.client import LLMClient, get_llm_client
from app.security.rate_limit import RateLimiter, limit_by_ip
from app.security.visitor import visitor_id

router = APIRouter(prefix="/api")

JOBFIT_LIMITERS = (RateLimiter(5, timedelta(days=1)),)
jobfit_limits = limit_by_ip(*JOBFIT_LIMITERS)

FALLBACK_TEXT = {
    "fa": "بررسی تناسب شغلی موقتاً خاموش است. رزومه را ببینید یا به {email} ایمیل بزنید.",
    "en": "The job fit check is temporarily off. Please see the resume or email {email}.",
}


class JobFitBody(BaseModel):
    job_ad: str = Field(min_length=50, max_length=6000)
    lang: Literal["fa", "en"]


@router.post("/jobfit", dependencies=[Depends(jobfit_limits)])
async def jobfit(
    body: JobFitBody,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    client: Annotated[LLMClient, Depends(get_llm_client)],
) -> FitResult:
    """Score the ad, store the request and return the result; 503 when AI is off."""
    try:
        result, completion = await check_fit(session, client, body.job_ad, body.lang)
    except BudgetExceeded:
        email = client.settings.contact_email
        raise HTTPException(503, FALLBACK_TEXT[body.lang].format(email=email))
    session.add(
        JobFitRequest(
            visitor_id=visitor_id(request, client.settings),
            jd_text=body.job_ad,
            lang=body.lang,
            score=result.score,
            result=result.model_dump(),
            model=client.settings.model_jobfit,
            tokens_in=completion.tokens_in,
            tokens_out=completion.tokens_out,
            cost_usd=completion.cost_usd,
        )
    )
    await session.commit()
    return result
