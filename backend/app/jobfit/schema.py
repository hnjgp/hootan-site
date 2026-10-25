"""Structured result of a job fit check; the model must fill exactly this shape."""

from pydantic import BaseModel, Field


class Strength(BaseModel):
    """A requirement Hootan meets, with the evidence from his profile."""

    point: str
    evidence: str


class FitResult(BaseModel):
    """Score 0-100, one-line summary, strengths, honest gaps and interview questions."""

    score: int = Field(ge=0, le=100)
    summary: str
    strengths: list[Strength]
    gaps: list[str] = Field(min_length=1)
    questions: list[str]
