from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, TypedDict, cast

from pydantic import SecretStr
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Query
from sqlalchemy.pool import AsyncAdaptedQueuePool, QueuePool

from {{ cookiecutter.repo_name }} import get_logger
from {{ cookiecutter.repo_name }}.app.core.utils import repr_obj

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable
    from typing import Any, Unpack

    from sqlalchemy import Pool
    from sqlalchemy.engine.interfaces import IsolationLevel
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSessionTransaction
    from sqlalchemy.log import _EchoFlagType
    from sqlalchemy.pool import _ResetStyleArgType
    from sqlalchemy.sql.base import _NoArg

__all__ = [
    "DEFAULT_ASYNC_ENGINE_PARAMS",
    "DEFAULT_ASYNC_SESSION_PARAMS",
    "SessionMakerT",
    "create_engine",
    "create_session",
    "create_sessionmaker",
    "dispose_engine",
]


SessionMakerT = async_sessionmaker[AsyncSession]


class AsyncEngineParams(TypedDict, total=False):
    """Engine options that `create_engine()` accepts as keyword overrides."""

    # If True, the engine logs every statement and a repr() of its parameters to a
    # handler that writes to standard output. The string "debug" also logs result rows.
    echo: _EchoFlagType

    # If True, the connection pool logs events such as connection invalidation and
    # recycling. The string "debug" also logs pool checkouts and checkins.
    echo_pool: _EchoFlagType

    isolation_level: IsolationLevel

    json_deserializer: Callable[..., Any]
    json_serializer: Callable[..., Any]

    # Number of connections that QueuePool can open beyond pool_size.
    max_overflow: int

    # Pool subclass that the engine instantiates with the connection parameters from the
    # URL. Set NullPool to disable pooling.
    poolclass: type[Pool] | None

    # If True, test each pooled connection for liveness on checkout.
    pool_pre_ping: bool

    # Number of connections to keep open in the pool. QueuePool treats 0 as no limit.
    pool_size: int

    # Age in seconds after which a pooled connection is replaced on checkout.
    pool_recycle: int

    # Reset that the pool applies to a connection on return: "rollback", "commit", or
    # None for no reset. The reset ends any transaction that user code left open.
    pool_reset_on_return: _ResetStyleArgType | None

    # Seconds that QueuePool waits for an available connection before it gives up.
    pool_timeout: float

    # If True, QueuePool retrieves connections in last-in-first-out order instead of
    # first-in-first-out order.
    pool_use_lifo: bool


class AsyncSessionParams(TypedDict, total=False):
    """Session options that `create_sessionmaker()` accepts as keyword overrides."""

    # If True, each query operation flushes the session before it runs.
    autoflush: bool

    # If True, an operation that requests database access begins a transaction when
    # none is active, as Session.begin() does.
    autobegin: bool

    # If True, each commit() expires all instances. Attribute and object access after
    # the commit loads the most recent database state.
    expire_on_commit: bool

    # If True, every transaction uses two-phase commit. Each bound database prepares the
    # transaction before any database commits it. Any database can therefore still roll
    # back the entire transaction. Two-phase commit serves a logical transaction that
    # spans several binds.
    twophase: bool

    # If True, close() resets the session for reuse. If False, close() leaves the
    # session unusable.
    close_resets_only: bool | _NoArg


# Constructor arguments of QueuePool and its subclasses.
_QUEUE_POOL_PARAMS = frozenset(
    {"max_overflow", "pool_size", "pool_timeout", "pool_use_lifo"}
)

DEFAULT_ASYNC_ENGINE_PARAMS: AsyncEngineParams = {
    "echo": False,
    "echo_pool": False,
    "isolation_level": "READ COMMITTED",
    "max_overflow": 10,
    "poolclass": AsyncAdaptedQueuePool,
    "pool_pre_ping": True,
    "pool_size": 10,
    # Keep this below the shortest idle timeout of any PgBouncer, load balancer, or NAT
    # in the connection path.
    "pool_recycle": 1800,
    # Roll back on return to release locks and transaction resources.
    "pool_reset_on_return": "rollback",
    "pool_timeout": 30.0,
    # Reuse the most recently returned connections first. Surplus idle connections can
    # then time out on the server during low traffic.
    "pool_use_lifo": True,
}

DEFAULT_ASYNC_SESSION_PARAMS: AsyncSessionParams = {
    "autoflush": True,
    "autobegin": True,
    # An attribute expired on commit refreshes implicitly on next access. Under asyncio,
    # that implicit I/O can run outside the async bridge and raise MissingGreenlet.
    #
    # Load relationships with selectinload() and fetch server-generated values with
    # `await session.refresh(obj, ["attr"])` instead.
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


def _merge_engine_params(params: AsyncEngineParams) -> AsyncEngineParams:
    """Returns DEFAULT_ASYNC_ENGINE_PARAMS overridden by `params`.

    The result omits the queue-pool defaults when the resulting `poolclass` lies outside
    the QueuePool hierarchy. Such pools reject those parameters. Values supplied in
    `params` are always kept.
    """
    merged: AsyncEngineParams = {**DEFAULT_ASYNC_ENGINE_PARAMS, **params}

    # None lets the dialect choose its default pool. For asyncio drivers, that default
    # is a queue pool.
    poolclass = merged.get("poolclass")
    if poolclass is None or issubclass(poolclass, QueuePool):
        return merged

    return cast(
        AsyncEngineParams,
        {k: v for k, v in merged.items() if k in params or k not in _QUEUE_POOL_PARAMS},
    )


def describe_engine(engine: AsyncEngine) -> None:
    """Logs the engine's connection pool metrics."""
    pool = getattr(engine, "pool", None)
    if not pool:
        logger.debug("Pool metrics not available for the database engine: %r", engine)
        return

    def _call(obj: Any, name: str, sentinel_: str = "not available") -> Any:
        func = getattr(obj, name, None)
        return func() if callable(func) else sentinel_

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

    Args:
        url: Database URL. A SecretStr is unwrapped before use. Logs show the URL
            with its password masked.
        raise_on_exc: If True, re-raise on failure instead of returning None.
        verbose: If True, log the created engine and its pool metrics.
        **params: Async engine parameters overriding the defaults.

    Returns:
        The new engine, or None if creation failed and raise_on_exc is False.

    Raises:
        SQLAlchemyError: If engine creation fails and raise_on_exc is True.
        TypeError: If a supplied parameter is invalid for the selected pool class,
            regardless of raise_on_exc.
    """
    merged = _merge_engine_params(params)

    try:
        # A `sqlalchemy.engine.URL` masks its password when printed, including in
        # traceback arguments.
        _url = make_url(url.get_secret_value() if isinstance(url, SecretStr) else url)

        engine = create_async_engine(_url, **merged)
    except SQLAlchemyError:
        logger.exception(
            "Error creating a database engine: `%s`",
            _redact_database_url(url),
            extra=merged,
        )
        if raise_on_exc:
            raise
        return None

    if verbose:
        logger.info("Database engine created: %r", engine)
        describe_engine(engine)

    return engine


async def dispose_engine(
    engine: AsyncEngine,
    *,
    verbose: bool = False,
) -> None:
    """Disposes a database engine, closing its pooled connections.

    SQLAlchemy errors raised during disposal are logged and suppressed.

    Args:
        engine: Engine to dispose.
        verbose: If True, log successful disposal.
    """
    assert engine, "database engine must be provided"
    try:
        await engine.dispose(
            # Close the connections checked in to the pool.
            close=True
        )
    except SQLAlchemyError:
        logger.exception(
            "Error disposing the database engine: %r",
            engine,
        )
        return

    if verbose:
        logger.info("Database engine disposed: %r", engine)


def create_sessionmaker(
    engine: AsyncEngine,
    *,
    verbose: bool = False,
    **params: Unpack[AsyncSessionParams],
) -> SessionMakerT:
    """Creates a session factory bound to an engine.

    Supplied parameters override DEFAULT_ASYNC_SESSION_PARAMS.

    Args:
        engine: Engine that the produced sessions bind to.
        verbose: If True, log the created session factory.
        **params: Async session parameters overriding the defaults.

    Returns:
        A session factory producing AsyncSession instances.
    """
    assert engine, "database engine must be provided"
    merged: AsyncSessionParams = {**DEFAULT_ASYNC_SESSION_PARAMS, **params}

    sessionmaker = async_sessionmaker(
        bind=engine, class_=AsyncSession, query_cls=Query, **merged
    )

    if verbose:
        logger.info(
            "Session factory %s created: %r", repr_obj(sessionmaker), sessionmaker
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

    The transaction commits when the caller's block completes. It rolls back when the
    block raises any exception, including asyncio.CancelledError. The session always
    closes when the block exits.

    Args:
        sessionmaker: Factory used to open the session.
        raise_on_exc: If True, re-raise SQLAlchemy and unexpected errors after rollback.
            CancelledError is re-raised regardless.
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
                logger.info("Database session created", extra=extra)

            try:
                async with session.begin() as tx:
                    extra.update({"transaction": repr_obj(tx)})
                    if verbose:
                        logger.info("Transaction started", extra=extra)

                    yield session

            except asyncio.CancelledError as exc:
                log_rollback("Task cancelled during transaction", exc)
                raise  # <- preserve the task cancellation

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
            logger.info("Database session closed", extra=extra)
