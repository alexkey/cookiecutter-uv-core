from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from {{ cookiecutter.repo_name }} import get_settings
from {{ cookiecutter.repo_name }}.app.db.database import (
    create_engine,
    create_sessionmaker,
    dispose_engine,
)

# Fixtures compose other fixtures by parameter name, which pylint reports as redefining
# the fixture function from the outer scope. That shadowing is how pytest injects
# fixtures and is intentional here.
# pylint: disable=redefined-outer-name

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator
    from typing import Any

    from sqlalchemy.ext.asyncio import AsyncEngine

    from {{ cookiecutter.repo_name }}.app.db.database import SessionMakerT

_DB_URL_VAR = "{{ cookiecutter.env_prefix }}DATABASE_URL"
_CONNECT_TIMEOUT = 5.0
_SCHEMA_PREFIX = "itest"


def _resolve_database_url() -> str | None:
    try:
        settings = get_settings(reload=True)
    except ValidationError:
        return None

    return settings.DATABASE_URL.get_secret_value()  # pylint: disable=no-member


@asynccontextmanager
async def _ephemeral_engine(url: str, **kwargs: Any) -> AsyncIterator[AsyncEngine]:
    """Yields a single-use NullPool engine, disposed when the block exits.
    """
    engine = create_async_engine(url, poolclass=NullPool, **kwargs)

    try:
        yield engine
    finally:
        await engine.dispose()


def _can_connect(url: str) -> bool:
    """Reports whether a connection to `url` can be established and queried."""

    async def _ping() -> None:
        async with _ephemeral_engine(
            url, connect_args={"timeout": _CONNECT_TIMEOUT}
        ) as engine:
            async with engine.connect() as conn:
                await conn.execute(sa_text("SELECT 1"))

    try:
        asyncio.run(_ping())
    except Exception:  # pylint: disable=broad-exception-caught
        return False

    return True


async def _run_ddl(url: str, statement: str) -> None:
    """Executes a single DDL statement."""
    async with _ephemeral_engine(url) as engine:
        async with engine.begin() as conn:
            await conn.execute(sa_text(statement))


@pytest.fixture(scope="session")
def database_url() -> str:
    url = _resolve_database_url()

    if not url:
        pytest.skip(f"{_DB_URL_VAR} is not set")

    if not _can_connect(url):
        pytest.skip(f"database for {_DB_URL_VAR} is not reachable")

    return url


@pytest.fixture(scope="session")
def database_schema(database_url: str) -> Iterator[str]:
    """A dedicated schema for the run, dropped with CASCADE afterward."""
    schema = f"{_SCHEMA_PREFIX}_{uuid4().hex[:8]}"

    def run_ddl(statement: str) -> None:
        asyncio.run(_run_ddl(database_url, statement))

    run_ddl(f"CREATE SCHEMA {schema}")
    try:
        yield schema
    finally:
        run_ddl(f"DROP SCHEMA {schema} CASCADE")


@pytest.fixture
async def database_engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    """A real engine bound to the configured database, disposed after the test."""
    engine = create_engine(database_url, raise_on_exc=True)

    assert engine is not None
    try:
        yield engine
    finally:
        await dispose_engine(engine)


@pytest.fixture
def database_sessionmaker(database_engine: AsyncEngine) -> SessionMakerT:
    """A session factory bound to the real engine."""
    return create_sessionmaker(database_engine)


@pytest.fixture
async def items_table(
    database_engine: AsyncEngine, database_schema: str
) -> AsyncIterator[str]:
    """Creates an isolated throwaway table in the run schema and drops it after."""
    table = f"{database_schema}.items"

    async with database_engine.begin() as conn:
        await conn.execute(sa_text(f"DROP TABLE IF EXISTS {table}"))
        await conn.execute(sa_text(f"CREATE TABLE {table} (id integer PRIMARY KEY)"))

    try:
        yield table
    finally:
        async with database_engine.begin() as conn:
            await conn.execute(sa_text(f"DROP TABLE IF EXISTS {table}"))
