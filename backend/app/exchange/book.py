"""Positions in the database: cash, equity, opening, closing and the automatic checks.

An owner is a player id, or None for the AI team. Cash is never stored; it is
START_USD plus every closed position's net result minus what open positions hold
(margin and opening fee), so it cannot drift from the positions.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EquitySnapshot, Player, Position
from app.exchange import calc

Owner = uuid.UUID | None


class OrderError(ValueError):
    """An order the exchange refuses; the message is a short code for the page."""


@dataclass
class Book:
    """One owner's cash and open positions."""

    cash: Decimal = calc.START_USD
    open: list[Position] = field(default_factory=list)

    def equity(self, price: Decimal) -> Decimal:
        """Cash plus what every open position is worth at `price`."""
        return calc.cents(
            self.cash + sum((stake(p, price) for p in self.open), Decimal(0))
        )


def pnl(p: Position, price: Decimal) -> Decimal:
    """Floating profit or loss of an open position before fees."""
    return calc.gross_pnl(p.side, p.qty, p.entry_price, price)


def stake(p: Position, price: Decimal) -> Decimal:
    """What an open position adds to equity at `price`."""
    return calc.stake(p.margin_usd, pnl(p, price))


def owned_by(owner: Owner):
    """SQL filter for one owner's positions."""
    return (
        Position.player_id.is_(None) if owner is None else Position.player_id == owner
    )


async def books(db: AsyncSession, *where) -> dict[Owner, Book]:
    """Books of every owner with a position, narrowed by optional SQL filters."""
    is_open = Position.closed_at.is_(None)
    query = select(
        Position.player_id,
        func.coalesce(func.sum(Position.pnl_usd).filter(~is_open), 0),
        func.coalesce(
            func.sum(Position.margin_usd + Position.fee_usd).filter(is_open), 0
        ),
    ).group_by(Position.player_id)
    opens = select(Position).where(is_open, *where).order_by(Position.id)
    query = query.where(*where)
    out = {
        who: Book(calc.START_USD + closed - held)
        for who, closed, held in await db.execute(query)
    }
    for p in await db.scalars(opens):
        out[p.player_id].open.append(p)
    return out


async def load_book(db: AsyncSession, owner: Owner) -> Book:
    """One owner's book; a new owner has START_USD and nothing open."""
    return (await books(db, owned_by(owner))).get(owner, Book())


async def open_position(
    db: AsyncSession,
    owner: Owner,
    side: str,
    margin: Decimal,
    leverage: int,
    price: Decimal,
    tp: Decimal | None = None,
    sl: Decimal | None = None,
    session_id: int | None = None,
) -> Position:
    """Open at `price`, paying margin and fee from cash; raise OrderError when refused.

    A player's row is locked first, so two orders at once cannot spend the same cash.
    """
    if owner is not None:
        await db.scalar(select(Player.id).where(Player.id == owner).with_for_update())
    cash = (await load_book(db, owner)).cash
    margin = calc.cents(margin)
    if margin < 1:
        raise OrderError("margin")
    if margin > calc.max_margin(cash, leverage):
        raise OrderError("cash")
    liq = calc.liq_price(side, price, leverage)
    if problem := calc.check_levels(side, price, liq, tp, sl):
        raise OrderError(problem)
    position = Position(
        player_id=owner,
        session_id=session_id,
        side=side,
        entry_price=price,
        margin_usd=margin,
        leverage=leverage,
        qty=calc.quantity(margin, leverage, price),
        tp_price=tp,
        sl_price=sl,
        liq_price=liq,
        fee_usd=calc.fee(margin, leverage),
    )
    db.add(position)
    await db.flush()
    return position


def settle(p: Position, price: Decimal, reason: str, now: datetime) -> None:
    """Close `p` at `price`: a liquidation loses the margin, otherwise pay the fee."""
    opening_fee = p.fee_usd
    if reason == "liq":
        returned = Decimal(0)
    else:
        closing_fee = calc.fee(p.margin_usd, p.leverage)
        returned = calc.payout(p.margin_usd, pnl(p, price), closing_fee)
        p.fee_usd += closing_fee
    p.closed_at, p.close_price, p.close_reason = now, price, reason
    p.pnl_usd = returned - p.margin_usd - opening_fee


async def close_position(
    db: AsyncSession, owner: Owner, position_id: int, price: Decimal, reason: str
) -> Position | None:
    """Close one open position of `owner`; None when there is no such open position.

    The row is locked, so the worker and the owner cannot close it twice.
    """
    p = await db.scalar(
        select(Position)
        .where(Position.id == position_id, owned_by(owner))
        .where(Position.closed_at.is_(None))
        .with_for_update()
    )
    if p is not None:
        settle(p, price, reason, datetime.now(UTC))
    return p


async def check_triggers(db: AsyncSession, price: Decimal) -> list[Position]:
    """Close every open position whose liquidation, stop loss or take profit was reached."""
    hit = []
    now = datetime.now(UTC)
    for p in await db.scalars(
        select(Position).where(Position.closed_at.is_(None)).with_for_update()
    ):
        if reason := calc.trigger(p.side, price, p.liq_price, p.tp_price, p.sl_price):
            settle(p, price, reason, now)
            hit.append(p)
    await db.commit()
    return hit


async def take_snapshots(db: AsyncSession, price: Decimal, day: date) -> None:
    """The day's equity of every player and the team, once per owner and day."""
    found = await books(db)
    owners = [None, *await db.scalars(select(Player.id))]
    rows = [
        {
            "day": day,
            "player_id": owner,
            "equity_usd": found.get(owner, Book()).equity(price),
            "price": price,
        }
        for owner in owners
    ]
    await db.execute(insert(EquitySnapshot).values(rows).on_conflict_do_nothing())
    await db.commit()


async def first_snapshot(
    db: AsyncSession, owner: Owner, since: date | None = None
) -> EquitySnapshot | None:
    """The owner's earliest snapshot, optionally on or after a day."""
    query = select(EquitySnapshot).where(
        EquitySnapshot.player_id.is_(None)
        if owner is None
        else EquitySnapshot.player_id == owner
    )
    if since is not None:
        query = query.where(EquitySnapshot.day >= since)
    return await db.scalar(query.order_by(EquitySnapshot.day).limit(1))


def position_out(p: Position, price: Decimal) -> dict:
    """A position for the page; open ones carry their floating P&L at `price`."""
    out = {
        "id": p.id,
        "side": p.side,
        "entry_price": p.entry_price,
        "margin_usd": p.margin_usd,
        "leverage": p.leverage,
        "qty": p.qty,
        "tp_price": p.tp_price,
        "sl_price": p.sl_price,
        "liq_price": p.liq_price,
        "fee_usd": p.fee_usd,
        "opened_at": p.opened_at,
        "closed_at": p.closed_at,
        "close_price": p.close_price,
        "close_reason": p.close_reason,
        "pnl_usd": p.pnl_usd,
    }
    if p.closed_at is None:
        out["pnl_usd"] = calc.cents(max(pnl(p, price), -p.margin_usd))
    return out
