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
from {{ cookiecutter.repo_name }}.logging import setup_logging
from tests.utils import fail_without_traceback

# Fixtures compose other fixtures by parameter name, which pylint reports as redefining
# the fixture function from the outer scope. That shadowing is how pytest injects
# fixtures and is intentional here.
# pylint: disable=redefined-outer-name

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Iterator
    from typing import Any

    from pydantic import SecretStr
    from sqlalchemy.ext.asyncio import AsyncEngine

    from {{ cookiecutter.repo_name }}.app.db.database import SessionMakerT

_DB_URL_VAR = "{{ cookiecutter.env_prefix }}DATABASE_URL"
_CONNECT_TIMEOUT = 5.0
_SCHEMA_PREFIX = "itest"


def _resolve_database_url() -> SecretStr | None:
    """Returns the configured database URL, or None if it is not set.

    Raises:
        ValidationError: If any other required setting is missing or a setting is
            invalid.
    """
    try:
        settings = get_settings(reload=True)
    except ValidationError as exc:
        if all(
            error["type"] == "missing" and error["loc"] == ("DATABASE_URL",)
            for error in exc.errors()
        ):
            return None
        raise

    return settings.DATABASE_URL


@asynccontextmanager
async def _ephemeral_engine(
    url: SecretStr, **kwargs: Any
) -> AsyncGenerator[AsyncEngine]:
    """Yields a single-use NullPool engine, disposed when the block exits."""
    engine = create_async_engine(url.get_secret_value(), poolclass=NullPool, **kwargs)

    try:
        yield engine
    finally:
        await engine.dispose()


def _check_connection(url: SecretStr) -> None:
    """Raises the underlying error unless `url` can be connected to and queried."""

    async def _ping() -> None:
        async with (
            _ephemeral_engine(
                url, connect_args={"timeout": _CONNECT_TIMEOUT}
            ) as engine,
            engine.connect() as conn,
        ):
            await conn.execute(sa_text("SELECT 1"))

    asyncio.run(_ping())


async def _run_ddl(url: SecretStr, statement: str) -> None:
    """Executes a single DDL statement."""
    async with _ephemeral_engine(url) as engine, engine.begin() as conn:
        await conn.execute(sa_text(statement))


@pytest.fixture(scope="session", autouse=True)
def app_logging() -> None:
    """Configures logging as the application does."""
    setup_logging("debug", "console")


@pytest.fixture(scope="session")
def database_url() -> SecretStr:
    try:
        url = _resolve_database_url()
    except ValidationError as exc:
        # The error input holds the raw URL, including its password.
        reasons = "; ".join(
            f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
            for error in exc.errors(include_input=False)
        )
        fail_without_traceback(f"invalid settings: {reasons}")

    # Explicit because an empty `SecretStr` evaluates to `False`.
    if url is None:
        fail_without_traceback(
            f"{_DB_URL_VAR} is not set; pass --skip-db to skip these tests"
        )

    try:
        _check_connection(url)
    except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        fail_without_traceback(f"database for {_DB_URL_VAR} is not reachable: {exc!r}")

    return url


@pytest.fixture(scope="session")
def database_schema(database_url: SecretStr) -> Iterator[str]:
    """A dedicated schema for the run, dropped with CASCADE afterward."""
    schema = f"{_SCHEMA_PREFIX}_{uuid4().hex[:8]}"

    def run_ddl(statement: str) -> None:
        asyncio.run(_run_ddl(database_url, statement))

    try:
        run_ddl(f"CREATE SCHEMA {schema}")
    except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
        fail_without_traceback(f"cannot create schema {schema}: {exc!r}")

    try:
        yield schema
    finally:
        try:
            run_ddl(f"DROP SCHEMA {schema} CASCADE")
        except Exception as exc:  # noqa: BLE001  # pylint: disable=broad-exception-caught
            fail_without_traceback(f"cannot drop schema {schema}: {exc!r}")


@pytest.fixture
async def database_engine(database_url: SecretStr) -> AsyncIterator[AsyncEngine]:
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
