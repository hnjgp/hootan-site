"""Structured replies of the trader and the portfolio manager.

The reason comes first so the model argues before it commits to numbers.
Limits here only reject nonsense; the risk rules are enforced in code (risk.py).
"""

from typing import Literal

from pydantic import BaseModel, Field


class PositionCall(BaseModel):
    """Keep or close one open position, by its id."""

    id: int
    action: Literal["hold", "close"]


class NewPosition(BaseModel):
    """A position to open: margin as a percent of equity; take profit and stop loss
    as a percent price move from the entry (take_profit_pct 0 means none)."""

    side: Literal["long", "short"]
    margin_pct: float = Field(ge=0, le=100)
    leverage: int = Field(ge=1, le=100)
    take_profit_pct: float = Field(ge=0, le=100)
    stop_loss_pct: float = Field(ge=0, le=100)


class TraderProposal(BaseModel):
    """A call for every open position and at most one new position (None for none)."""

    reason: str
    positions: list[PositionCall]
    new_position: NewPosition | None


class PMDecision(BaseModel):
    """Final approval of the whole checked plan."""

    reason: str
    approve: bool
