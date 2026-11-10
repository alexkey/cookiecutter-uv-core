from __future__ import annotations

import asyncio
import io
from collections.abc import Callable
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast, get_origin

import pytest
from pydantic import SecretStr
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import NoSuchModuleError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Query
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool, StaticPool

from {{ cookiecutter.repo_name }}.app.db import database
from {{ cookiecutter.repo_name }}.app.db.database import (
    DEFAULT_ASYNC_ENGINE_PARAMS,
    DEFAULT_ASYNC_SESSION_PARAMS,
    SessionMakerT,
    _redact_database_url,
    create_engine,
    create_session,
    create_sessionmaker,
    describe_engine,
    dispose_engine,
)
from tests.utils import assert_log_event, assert_log_exception, parse_json_lines

if TYPE_CHECKING:
    from typing import Never

    from tests.main.app.db.conftest import FakeSessionMaker

_INVALID_DRIVER = "postgresql+nosuchdriver"

_TRANSACTION_ERRORS = [
    pytest.param(
        SQLAlchemyError, "Database error during transaction", id="sqlalchemy-error"
    ),
    pytest.param(
        RuntimeError, "Unexpected error during transaction", id="unexpected-error"
    ),
]


class _EngineWithFailingDispose:
    async def dispose(self, **_kwargs: object) -> Never:
        raise SQLAlchemyError("dispose failed")


class TestRedactDatabaseUrl:
    @pytest.mark.parametrize(
        "to_input",
        [
            pytest.param(str, id="str"),
            pytest.param(SecretStr, id="secret-str"),
            pytest.param(make_url, id="url-object"),
        ],
    )
    def test_masks_password(
        self,
        to_input: Callable[[str], str | SecretStr | URL],
        valid_database_url: str,
        make_database_url: Callable[..., str],
    ) -> None:
        result = _redact_database_url(to_input(valid_database_url))
        assert result == make_database_url(password="***")

    def test_renders_url_without_password(
        self, make_database_url: Callable[..., str]
    ) -> None:
        url = make_database_url(password=None)
        assert _redact_database_url(url) == url

    def test_returns_sentinel_for_invalid_url(self) -> None:
        assert _redact_database_url("not/a/valid/url") == "<invalid database URL>"


class TestCreateEngine:
    def test_creates_engine_for_async_url(
        self,
        valid_database_url: str,
        database_driver: str,
        database_user: str,
        database_port: int,
        database_name: str,
    ) -> None:
        engine = create_engine(valid_database_url)
        assert isinstance(engine, AsyncEngine)
        assert engine.url.drivername == database_driver
        assert engine.url.username == database_user
        assert engine.url.port == database_port
        assert engine.url.database == database_name

    def test_unwraps_secret_str_url(
        self, valid_database_url: str, database_password: str
    ) -> None:
        engine = create_engine(SecretStr(valid_database_url))
        assert isinstance(engine, AsyncEngine)
        assert engine.url.password == database_password

    def test_applies_engine_defaults(self, valid_database_url: str) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        pool = engine.pool
        assert isinstance(pool, AsyncAdaptedQueuePool)
        assert pool.size() == DEFAULT_ASYNC_ENGINE_PARAMS["pool_size"]

    def test_overrides_engine_defaults(self, valid_database_url: str) -> None:
        engine = create_engine(valid_database_url, echo=True, pool_size=3)
        assert engine is not None
        assert engine.echo is True
        pool = engine.pool
        assert isinstance(pool, AsyncAdaptedQueuePool)
        assert pool.size() == 3

    @pytest.mark.parametrize("poolclass", [NullPool, StaticPool])
    def test_creates_engine_with_non_queue_pool(
        self, valid_database_url: str, poolclass: type[NullPool | StaticPool]
    ) -> None:
        engine = create_engine(valid_database_url, poolclass=poolclass)
        assert engine is not None
        assert isinstance(engine.pool, poolclass)

    def test_passes_supplied_queue_pool_params_to_non_queue_pool(
        self, valid_database_url: str
    ) -> None:
        with pytest.raises(TypeError, match="pool_size"):
            create_engine(valid_database_url, poolclass=NullPool, pool_size=3)

    def test_logs_engine_and_pool_when_verbose(
        self, cap_json_logs: io.StringIO, valid_database_url: str
    ) -> None:
        create_engine(valid_database_url, verbose=True)
        assert_log_event(cap_json_logs, "Created new database engine", level="info")
        assert_log_event(cap_json_logs, "Database connection pool", level="info")

    def test_returns_none_on_failure(
        self, cap_json_logs: io.StringIO, make_database_url: Callable[..., str]
    ) -> None:
        url = make_database_url(driver=_INVALID_DRIVER)
        assert create_engine(url) is None
        assert_log_exception(
            cap_json_logs, "Error creating a new database engine", "NoSuchModuleError"
        )

    def test_raises_on_failure_when_requested(
        self, cap_json_logs: io.StringIO, make_database_url: Callable[..., str]
    ) -> None:
        url = make_database_url(driver=_INVALID_DRIVER)
        with pytest.raises(NoSuchModuleError):
            create_engine(url, raise_on_exc=True)
        assert_log_exception(
            cap_json_logs, "Error creating a new database engine", "NoSuchModuleError"
        )

    def test_logs_masked_url_on_failure(
        self,
        cap_json_logs: io.StringIO,
        make_database_url: Callable[..., str],
        database_password: str,
    ) -> None:
        url = make_database_url(driver=_INVALID_DRIVER)
        assert create_engine(url) is None
        masked_url = make_database_url(driver=_INVALID_DRIVER, password="***")
        assert_log_event(cap_json_logs, f"URL -> `{masked_url}`")
        assert database_password not in cap_json_logs.getvalue()


class TestDescribeEngine:
    def test_logs_pool_metrics(
        self, cap_json_logs: io.StringIO, valid_database_url: str
    ) -> None:
        engine = create_engine(valid_database_url, pool_size=3, pool_timeout=7.5)
        assert engine is not None
        describe_engine(engine)
        # A new queue pool has no checked-out connections and reports its overflow as
        # the negated pool size.
        assert_log_event(
            cap_json_logs,
            "size=3, checkedout=0, overflow=-3, timeout=7.5",
            level="info",
        )

    def test_marks_metrics_the_pool_does_not_provide(
        self, cap_json_logs: io.StringIO, valid_database_url: str
    ) -> None:
        engine = create_engine(valid_database_url, poolclass=NullPool)
        assert engine is not None
        describe_engine(engine)
        assert_log_event(
            cap_json_logs,
            "size=not available, checkedout=not available, "
            "overflow=not available, timeout=not available",
            level="info",
        )

    def test_reports_when_pool_unavailable(self, cap_json_logs: io.StringIO) -> None:
        describe_engine(cast(AsyncEngine, SimpleNamespace(pool=None)))
        assert_log_event(cap_json_logs, "Pool metrics not available", level="debug")


class TestDisposeEngine:
    async def test_discards_the_connection_pool(self, valid_database_url: str) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        pool = engine.pool
        await dispose_engine(engine)
        assert engine.pool is not pool

    async def test_requires_an_engine(self) -> None:
        with pytest.raises(AssertionError, match="engine instance must be provided"):
            await dispose_engine(cast(AsyncEngine, None))

    async def test_suppresses_disposal_errors(self, cap_json_logs: io.StringIO) -> None:
        await dispose_engine(cast(AsyncEngine, _EngineWithFailingDispose()))
        assert_log_exception(
            cap_json_logs,
            "Error occurred during database engine disposal",
            "SQLAlchemyError",
            exc_value="dispose failed",
        )

    async def test_logs_success_when_verbose(
        self, cap_json_logs: io.StringIO, valid_database_url: str
    ) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        await dispose_engine(engine, verbose=True)
        assert_log_event(cap_json_logs, "disposed successfully")


class TestCreateSessionmaker:
    def test_returns_factory_bound_to_engine(self, valid_database_url: str) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        factory = create_sessionmaker(engine)
        assert isinstance(factory, async_sessionmaker)
        assert factory.kw["bind"] is engine
        assert factory.kw["query_cls"] is Query
        assert factory.class_ is AsyncSession

    def test_applies_session_defaults(self, valid_database_url: str) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        factory = create_sessionmaker(engine)
        applied = {name: factory.kw[name] for name in DEFAULT_ASYNC_SESSION_PARAMS}
        assert applied == DEFAULT_ASYNC_SESSION_PARAMS

    def test_overrides_session_defaults(self, valid_database_url: str) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        factory = create_sessionmaker(engine, expire_on_commit=True)
        assert factory.kw["expire_on_commit"] is True

    def test_requires_an_engine(self) -> None:
        with pytest.raises(AssertionError, match="engine instance must be provided"):
            create_sessionmaker(cast(AsyncEngine, None))

    def test_logs_when_verbose(
        self, cap_json_logs: io.StringIO, valid_database_url: str
    ) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        create_sessionmaker(engine, verbose=True)
        assert_log_event(cap_json_logs, "Created new session factory")


class TestCreateSession:
    async def test_yields_session_within_a_transaction(
        self, make_fake_sessionmaker: Callable[[], FakeSessionMaker]
    ) -> None:
        fake = make_fake_sessionmaker()
        async with create_session(cast(SessionMakerT, fake)) as session:
            assert session is fake.session
            assert fake.session.begin_called is True
            assert fake.session.transaction.entered is True

    async def test_commits_and_closes_on_success(
        self, make_fake_sessionmaker: Callable[[], FakeSessionMaker]
    ) -> None:
        fake = make_fake_sessionmaker()
        async with create_session(cast(SessionMakerT, fake)):
            pass
        assert fake.session.transaction.exit_exc_type is None
        assert fake.session.transaction.exited is True
        assert fake.session.closed is True

    @pytest.mark.parametrize(("error_type", "cause"), _TRANSACTION_ERRORS)
    async def test_rolls_back_and_reraises_by_default(
        self,
        cap_json_logs: io.StringIO,
        make_fake_sessionmaker: Callable[[], FakeSessionMaker],
        error_type: type[Exception],
        cause: str,
    ) -> None:
        fake = make_fake_sessionmaker()
        with pytest.raises(error_type, match="boom"):
            async with create_session(cast(SessionMakerT, fake)):
                raise error_type("boom")
        assert fake.session.transaction.exit_exc_type is error_type
        assert fake.session.closed is True
        assert_log_exception(
            cap_json_logs, cause, error_type.__name__, exc_value="boom"
        )
        assert_log_event(cap_json_logs, "Transaction rolled back", level="error")

    @pytest.mark.parametrize(("error_type", "cause"), _TRANSACTION_ERRORS)
    async def test_rolls_back_and_suppresses_when_not_raising(
        self,
        cap_json_logs: io.StringIO,
        make_fake_sessionmaker: Callable[[], FakeSessionMaker],
        error_type: type[Exception],
        cause: str,
    ) -> None:
        fake = make_fake_sessionmaker()
        async with create_session(cast(SessionMakerT, fake), raise_on_exc=False):
            raise error_type("boom")
        assert fake.session.transaction.exit_exc_type is error_type
        assert fake.session.closed is True
        assert_log_exception(
            cap_json_logs, cause, error_type.__name__, exc_value="boom"
        )
        assert_log_event(cap_json_logs, "Transaction rolled back", level="error")

    async def test_reraises_task_cancellation_even_when_not_raising(
        self,
        cap_json_logs: io.StringIO,
        make_fake_sessionmaker: Callable[[], FakeSessionMaker],
    ) -> None:
        fake = make_fake_sessionmaker()
        with pytest.raises(asyncio.CancelledError):
            async with create_session(cast(SessionMakerT, fake), raise_on_exc=False):
                raise asyncio.CancelledError
        assert fake.session.transaction.exit_exc_type is asyncio.CancelledError
        assert fake.session.closed is True
        assert_log_exception(
            cap_json_logs,
            "Database session cancelled by asyncio task",
            "CancelledError",
        )

    async def test_logs_lifecycle_with_context_when_verbose(
        self,
        cap_json_logs: io.StringIO,
        make_fake_sessionmaker: Callable[[], FakeSessionMaker],
    ) -> None:
        fake = make_fake_sessionmaker()
        async with create_session(
            cast(SessionMakerT, fake), verbose=True, context="job-42"
        ):
            pass
        # The capture also holds debug records from other loggers, such as asyncio
        # reporting its selector while the event loop starts.
        records = [
            record
            for record in parse_json_lines(cap_json_logs)
            if record["logger"] == database.__name__
        ]
        assert [record["event"] for record in records] == [
            "Created new database session",
            "Began transaction",
            "Transaction committed",
            "Transaction closed",
            "Session closed",
        ]
        contexts = [record.get("extra", {}).get("context") for record in records]
        assert contexts == ["job-42"] * len(records)


class TestPublicApi:
    def test_dunder_all_lists_public_helpers(self) -> None:
        assert set(database.__all__) == {
            # pylint: disable=duplicate-code
            "SessionMakerT",
            "DEFAULT_ASYNC_ENGINE_PARAMS",
            "DEFAULT_ASYNC_SESSION_PARAMS",
            "create_engine",
            "dispose_engine",
            "create_sessionmaker",
            "create_session",
        }

    def test_exposes_session_maker_type_alias(self) -> None:
        assert get_origin(SessionMakerT) is async_sessionmaker
