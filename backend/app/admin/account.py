"""Create or update Hootan's admin account (sign-up refuses the admin nickname).

Run on the server: python -m app.admin.account <email>  (asks for the password,
so it stays out of the shell history)
"""

import asyncio
import sys
from getpass import getpass

from sqlalchemy import select

from app.config import get_settings
from app.db.models import MarketPrice, Player
from app.db.session import SessionLocal
from app.game.accounts import by_nickname


async def main(password: str, email: str) -> None:
    """Set the admin's password and email, creating the account if it is missing."""
    nickname = get_settings().admin_nickname
    async with SessionLocal() as session:
        player = await by_nickname(session, nickname)
        if player is None:
            price = await session.scalar(
                select(MarketPrice.price).order_by(MarketPrice.ts.desc()).limit(1)
            )
            player = Player(nickname=nickname, signup_price=price)
            session.add(player)
        player.password = password
        player.email = email
        await session.commit()
        print(f"{nickname}: saved")


if __name__ == "__main__":
    asyncio.run(main(getpass("Password: "), sys.argv[1]))
