"""Integration fixtures: a fresh migrated test database; each test rolls back."""

import asyncio
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


async def recreate_database(admin_url, name: str) -> None:
    """Drop and create the test database using a connection to the main database."""
    engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")
    async with engine.connect() as conn:
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        await conn.execute(text(f'CREATE DATABASE "{name}"'))
    await engine.dispose()


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """URL of a freshly created test database migrated to head."""
    main_url = make_url(get_settings().database_url)
    test_url = main_url.set(database=f"{main_url.database}_test")
    asyncio.run(recreate_database(main_url, test_url.database))

    config = Config(ALEMBIC_INI)
    config.attributes["url"] = test_url.render_as_string(hide_password=False)
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")
    return config.attributes["url"]


@pytest.fixture
async def session(test_db_url):
    """Session inside an outer transaction that is rolled back after the test."""
    engine = create_async_engine(test_db_url, poolclass=NullPool)
    async with engine.connect() as conn:
        outer = await conn.begin()
        async with AsyncSession(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as s:
            yield s
        await outer.rollback()
    await engine.dispose()
