"""Structured result of a job fit check; the model must fill exactly this shape.

Fields are generated in order, so the requirement check comes first and the score
last: with the score first, the model fixed it before weighing anything and ignored
the rubric caps (real test, 2026-10-26).
"""

from typing import Literal

from pydantic import BaseModel, Field


class Requirement(BaseModel):
    """One requirement of the ad and whether the profile shows it."""

    requirement: str
    kind: Literal["skill", "experience"]
    must_have: bool
    status: Literal["met", "partial", "missing"]
    note: str


class Strength(BaseModel):
    """A requirement Hootan meets, with the evidence from his profile."""

    point: str
    evidence: str


class FitResult(BaseModel):
    """Requirement check, strengths, honest gaps, summary, questions, then the score."""

    requirements: list[Requirement]
    strengths: list[Strength]
    gaps: list[str] = Field(min_length=1)
    summary: str
    questions: list[str]
    score: int = Field(ge=0, le=100)
