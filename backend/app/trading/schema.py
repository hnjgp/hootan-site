"""Structured replies of the trader and the portfolio manager.

The reason comes first so the model argues before it commits to a number.
Limits here only reject nonsense; the risk rules are enforced in code (risk.py).
"""

from typing import Literal

from pydantic import BaseModel, Field


class TraderProposal(BaseModel):
    """BUY puts size_pct of the portfolio value into BTC; SELL sells size_pct of the BTC held."""

    reason: str
    action: Literal["BUY", "SELL", "HOLD"]
    size_pct: float = Field(ge=0, le=100)


class PMDecision(BaseModel):
    """Final approval of the checked proposal and the stop loss for a new position."""

    reason: str
    approve: bool
    stop_loss_pct: float = Field(ge=0, le=100)
