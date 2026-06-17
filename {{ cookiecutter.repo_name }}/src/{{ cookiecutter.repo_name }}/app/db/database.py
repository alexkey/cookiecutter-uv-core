from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, TypedDict

from pydantic import SecretStr
from sqlalchemy.engine import URL, make_url
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Query

from {{ cookiecutter.repo_name }} import get_logger
from {{ cookiecutter.repo_name }}.app.core.utils import repr_obj

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from typing import Any, Callable, Unpack

    from sqlalchemy import Pool
    from sqlalchemy.engine.interfaces import IsolationLevel
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSessionTransaction
    from sqlalchemy.log import _EchoFlagType
    from sqlalchemy.pool import _ResetStyleArgType
    from sqlalchemy.sql.base import _NoArg

__all__ = [
    "SessionMakerT",
    "DEFAULT_ASYNC_ENGINE_PARAMS",
    "DEFAULT_ASYNC_SESSION_PARAMS",
    "create_engine",
    "dispose_engine",
    "create_sessionmaker",
    "create_session",
]


SessionMakerT = async_sessionmaker[AsyncSession]


class AsyncEngineParams(TypedDict, total=False):
    # If True, the Engine will log all statements as well as a repr() of their parameter
    # lists to the default log handler.
    echo: _EchoFlagType

    # If True, the connection pool will log informational output such as when
    # connections are invalidated as well as when connections are recycled.
    # If set to the string "debug", the logging will include pool checkouts and
    # checkins.
    echo_pool: _EchoFlagType

    isolation_level: IsolationLevel

    json_deserializer: Callable[..., Any]
    json_serializer: Callable[..., Any]

    # Number of connections that can be opened above and beyond the pool_size setting
    # (QueuePool only).
    max_overflow: int

    # Pool subclass, which will be used to create a connection pool instance using the
    # connection parameters given in the URL.
    # To disable pooling, set poolclass to NullPool instead.
    poolclass: type[Pool] | None

    # If True will test the pool connections for liveness upon each checkout.
    pool_pre_ping: bool

    # Number of connections to keep open inside the connection pool.
    # With QueuePool, a pool_size setting of 0 indicates no limit.
    pool_size: int

    # Number of seconds to recycle pool connections.
    pool_recycle: int

    # Determine steps to take on connections as they are returned to the pool,
    # especially when the connection wasn't explicitly cleaned up by user code.
    pool_reset_on_return: _ResetStyleArgType | None

    # Number of seconds to wait before giving up on getting a connection from the pool.
    # This is only used with QueuePool.
    pool_timeout: float

    # Use LIFO (last-in-first-out) when retrieving connections from QueuePool instead of
    # FIFO (first-in-first-out).
    pool_use_lifo: bool


class AsyncSessionParams(TypedDict, total=False):
    # When True, all query operations will issue a Session.flush() call to this Session
    # before proceeding.
    autoflush: bool

    # Automatically start transactions (equivalent to invoking Session.begin()).
    autobegin: bool

    # When True, all instances will be fully expired after each commit(), so that all
    # attribute/object access subsequent to a completed transaction will load from the
    # most recent database state.
    expire_on_commit: bool

    # When True, all transactions will be started as a "two phase" transaction.
    # This allows each database to roll back the entire transaction, before each
    # transaction is committed.
    # Typically used when you have multiple binds in one logical transaction.
    twophase: bool

    # Determines if the session should reset itself after calling .close() or should
    # pass in a no longer usable state, disabling re-use.
    close_resets_only: bool | _NoArg


DEFAULT_ASYNC_ENGINE_PARAMS: AsyncEngineParams = {
    "echo": False,
    "echo_pool": False,
    "isolation_level": "READ COMMITTED",
    "max_overflow": 10,
    "poolclass": AsyncAdaptedQueuePool,
    "pool_pre_ping": True,
    "pool_size": 10,
    # Set this below the PgBouncer/load balancer idle timeout when deploying behind one:
    "pool_recycle": 1800,
    # Call rollback() on the connection, to release locks and transaction resources:
    "pool_reset_on_return": "rollback",
    "pool_timeout": 30.0,
    # Allows unused connections to time out naturally on the server side, which is
    # beneficial in non-peak usage scenarios:
    "pool_use_lifo": True,
}

DEFAULT_ASYNC_SESSION_PARAMS: AsyncSessionParams = {
    "autoflush": True,
    "autobegin": True,
    # Expiration should generally not be needed as Session.expire_on_commit should
    # normally be set to False when using asyncio.
    #
    # In async, avoid implicit I/O (lazy loads) where possible; prefer selectinload() or
    # explicit `await session.refresh(obj, ["rel"])`.
    "expire_on_commit": False,
    "twophase": False,
    "close_resets_only": False,
}


logger = get_logger(__name__)


def _redact_database_url(url: str | SecretStr | URL) -> str:
    """Returns a log-safe rendering of a database URL with the password masked."""
    _url = url.get_secret_value() if isinstance(url, SecretStr) else url

    try:
        url_obj = _url if isinstance(_url, URL) else make_url(_url)
    except SQLAlchemyError:
        return "<invalid database URL>"

    return url_obj.render_as_string(hide_password=True)


def describe_engine(engine: AsyncEngine) -> None:
    """Logs the engine's connection pool metrics."""
    pool = getattr(engine, "pool", None)
    if not pool:
        logger.debug("Pool metrics not available for engine: %r", engine)
        return

    def _call(obj: Any, name: str, sentinel: str = "not available") -> Any:
        func = getattr(obj, name, None)
        return func() if callable(func) else sentinel

    logger.info(
        "Database connection pool %r: size=%s, checkedout=%s, overflow=%s, timeout=%s",
        pool,
        _call(pool, "size"),
        _call(pool, "checkedout"),
        _call(pool, "overflow"),
        _call(pool, "timeout"),
    )


def create_engine(
    url: str | SecretStr | URL,
    *,
    raise_on_exc: bool = False,
    verbose: bool = False,
    **params: Unpack[AsyncEngineParams],
) -> AsyncEngine | None:
    """Creates an async engine from a database URL.

    Supplied parameters override DEFAULT_ASYNC_ENGINE_PARAMS.

    Args:
        url: Database URL; a SecretStr is unwrapped before use and masked in logs.
        raise_on_exc: If True, re-raise on failure instead of returning None.
        verbose: If True, log the created engine and its pool metrics.
        **params: Async engine parameters overriding the defaults.

    Returns:
        The new engine, or None if creation failed and raise_on_exc is False.

    Raises:
        SQLAlchemyError: If engine creation fails and raise_on_exc is True.
    """
    merged: AsyncEngineParams = {**DEFAULT_ASYNC_ENGINE_PARAMS, **params}

    _url = url.get_secret_value() if isinstance(url, SecretStr) else url
    try:
        engine = create_async_engine(_url, **merged)
    except SQLAlchemyError:
        logger.error(
            "Error creating a new database engine: URL -> `%s`",
            _redact_database_url(url),
            extra=merged,
            exc_info=True,
        )
        if raise_on_exc:
            raise
        return None

    if verbose:
        logger.info("Created new database engine: %r", engine)
        describe_engine(engine)

    return engine


async def dispose_engine(
    engine: AsyncEngine,
    *,
    verbose: bool = False,
) -> None:
    """Disposes a database engine, closing its pooled connections.

    Disposal errors are logged and suppressed rather than propagated.

    Args:
        engine: Engine to dispose.
        verbose: If True, log successful disposal.
    """
    assert engine, "Database engine instance must be provided"
    try:
        await engine.dispose(
            # Close all currently checked in database connections:
            close=True
        )
    except SQLAlchemyError:
        logger.error(
            "Error occurred during database engine disposal: %r",
            engine,
            exc_info=True,
        )
        return

    if verbose:
        logger.info("Database engine disposed successfully: %r", engine)


def create_sessionmaker(
    engine: AsyncEngine,
    *,
    verbose: bool = False,
    **params: Unpack[AsyncSessionParams],
) -> SessionMakerT:
    """Creates a session factory bound to an engine.

    Supplied parameters override DEFAULT_ASYNC_SESSION_PARAMS.

    Args:
        engine: Engine that produced sessions are bound to.
        verbose: If True, log the created session factory.
        **params: Async session parameters overriding the defaults.

    Returns:
        A session factory producing AsyncSession instances.
    """
    assert engine, "Database engine instance must be provided"
    merged: AsyncSessionParams = {**DEFAULT_ASYNC_SESSION_PARAMS, **params}

    sessionmaker = async_sessionmaker(
        bind=engine, class_=AsyncSession, query_cls=Query, **merged
    )

    if verbose:
        logger.info(
            "Created new session factory %s: %r", repr_obj(sessionmaker), sessionmaker
        )

    return sessionmaker


@asynccontextmanager
async def create_session(
    sessionmaker: SessionMakerT,
    *,
    raise_on_exc: bool = True,
    verbose: bool = False,
    context: str = "default",
) -> AsyncGenerator[AsyncSession]:
    # pylint: disable=too-many-branches

    """Creates a new session and manages a single transaction.

    On success, the transaction is committed.
    On exception (including asyncio.CancelledError), the transaction is rolled back.
    The session is always closed upon exiting the caller's block.

    Args:
        sessionmaker: Factory used to open the session.
        raise_on_exc: If True, re-raise SQLAlchemy and unexpected errors after rollback;
            CancelledError is always re-raised.
        verbose: If True, log each lifecycle step.
        context: Label included in log records to correlate the session.

    Yields:
        An open AsyncSession enclosed in an active transaction.
    """
    extra: dict[str, Any] = {"context": context, "sessionmaker": repr_obj(sessionmaker)}

    session: AsyncSession | None = None
    tx: AsyncSessionTransaction | None = None

    def log_rollback(cause: str, exc: BaseException | None) -> None:
        logger.error(cause, extra=extra, exc_info=bool(exc))
        if tx:
            logger.error("Transaction rolled back", extra=extra)

    try:
        async with sessionmaker() as session:
            extra.update({"session": repr_obj(session)})
            if verbose:
                logger.info("Created new database session", extra=extra)

            try:
                async with session.begin() as tx:
                    extra.update({"transaction": repr_obj(tx)})
                    if verbose:
                        logger.info("Began transaction", extra=extra)

                    yield session

            except asyncio.CancelledError as exc:
                log_rollback("Database session cancelled by asyncio task", exc)
                raise  # <- preserve task cancellation

            except SQLAlchemyError as exc:
                log_rollback("Database error during transaction", exc)
                if raise_on_exc:
                    raise

            except Exception as exc:  # pylint: disable=broad-exception-caught
                log_rollback("Unexpected error during transaction", exc)
                if raise_on_exc:
                    raise

            else:  # <- no exception occurred
                if verbose:
                    logger.info("Transaction committed", extra=extra)

            finally:
                if verbose and tx:
                    logger.info("Transaction closed", extra=extra)

    finally:
        if verbose and session:
            logger.info("Session closed", extra=extra)
