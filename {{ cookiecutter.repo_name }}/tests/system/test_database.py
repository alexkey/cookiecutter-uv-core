from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text as sa_text
from sqlalchemy.pool import AsyncAdaptedQueuePool

from {{ cookiecutter.repo_name }}.app.db.database import (
    create_engine,
    create_session,
    create_sessionmaker,
    dispose_engine,
)

if TYPE_CHECKING:
    from {{ cookiecutter.repo_name }}.app.db.database import SessionMakerT


@pytest.mark.requires_db
class TestDatabaseRoundTrip:
    async def test_session_commits_persist_rows(
        self, database_sessionmaker: SessionMakerT, items_table: str
    ) -> None:
        async with create_session(database_sessionmaker) as session:
            await session.execute(
                sa_text(f"INSERT INTO {items_table} (id) VALUES (1), (2)")
            )

        async with create_session(database_sessionmaker) as session:
            result = await session.execute(
                sa_text(f"SELECT id FROM {items_table} ORDER BY id")
            )
            assert result.scalars().all() == [1, 2]

    async def test_session_rolls_back_on_error(
        self, database_sessionmaker: SessionMakerT, items_table: str
    ) -> None:
        async with create_session(database_sessionmaker, raise_on_exc=False) as session:
            await session.execute(sa_text(f"INSERT INTO {items_table} (id) VALUES (1)"))
            raise RuntimeError("force rollback")

        async with create_session(database_sessionmaker) as session:
            result = await session.execute(sa_text(f"SELECT id FROM {items_table}"))
            assert result.scalars().all() == []

    async def test_applies_isolation_level(self, database_url: str) -> None:
        engine = create_engine(
            database_url, raise_on_exc=True, isolation_level="SERIALIZABLE"
        )

        assert engine is not None
        try:
            factory = create_sessionmaker(engine)

            async with create_session(factory) as session:
                result = await session.execute(sa_text("SHOW transaction_isolation"))
                assert result.scalar_one() == "serializable"
        finally:
            await dispose_engine(engine)

    async def test_dispose_closes_pooled_connections(self, database_url: str) -> None:
        engine = create_engine(database_url, raise_on_exc=True)
        assert engine is not None

        async with engine.connect() as conn:
            await conn.execute(sa_text("SELECT 1"))

        pool = engine.pool
        assert isinstance(pool, AsyncAdaptedQueuePool)
        assert pool.checkedin() == 1

        await dispose_engine(engine)
        fresh_pool = engine.pool
        assert isinstance(fresh_pool, AsyncAdaptedQueuePool)
        assert fresh_pool.checkedin() == 0
