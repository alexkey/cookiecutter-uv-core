from __future__ import annotations

import asyncio
import io
from collections.abc import Callable
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast, get_origin

import pytest
from pydantic import SecretStr
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Query
from sqlalchemy.pool import AsyncAdaptedQueuePool

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
from tests.utils import assert_log_event_count, parse_json_lines

if TYPE_CHECKING:
    from tests.main.app.db.conftest import FakeSessionMaker

_INVALID_DRIVER = "postgresql+nosuchdriver"


class _EngineWithFailingDispose:
    async def dispose(self, **_kwargs: object) -> None:
        raise SQLAlchemyError("dispose failed")


class TestRedactDatabaseUrl:
    def test_masks_password_in_string_url(
        self,
        valid_database_url: str,
        database_password: str,
        database_user: str,
        database_host: str,
    ) -> None:
        result = _redact_database_url(valid_database_url)
        assert database_password not in result
        assert database_user in result
        assert database_host in result

    def test_masks_password_in_secret_str(
        self, valid_database_url: str, database_password: str, database_host: str
    ) -> None:
        result = _redact_database_url(SecretStr(valid_database_url))
        assert database_password not in result
        assert database_host in result

    def test_accepts_url_object(self, valid_database_url: str) -> None:
        url = make_url(valid_database_url)
        assert _redact_database_url(url) == url.render_as_string(hide_password=True)

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

    def test_returns_none_on_failure(
        self, make_database_url: Callable[..., str]
    ) -> None:
        url = make_database_url(driver=_INVALID_DRIVER)
        assert create_engine(url) is None

    def test_raises_on_failure_when_requested(
        self, make_database_url: Callable[..., str]
    ) -> None:
        url = make_database_url(driver=_INVALID_DRIVER)
        with pytest.raises(SQLAlchemyError):
            create_engine(url, raise_on_exc=True)

    def test_does_not_leak_password_on_failure(
        self,
        cap_json_logs: io.StringIO,
        make_database_url: Callable[..., str],
        database_password: str,
    ) -> None:
        url = make_database_url(driver=_INVALID_DRIVER)
        assert create_engine(url) is None
        output = cap_json_logs.getvalue()
        assert database_password not in output
        assert "Error creating a new database engine" in output


class TestDescribeEngine:
    def test_logs_pool_metrics(
        self, cap_json_logs: io.StringIO, valid_database_url: str
    ) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        describe_engine(engine)
        record = parse_json_lines(cap_json_logs)[-1]
        assert record["event"].startswith("Database connection pool")
        assert "size=" in record["event"]
        assert record["level"] == "info"

    def test_reports_when_pool_unavailable(self, cap_json_logs: io.StringIO) -> None:
        describe_engine(cast(AsyncEngine, SimpleNamespace(pool=None)))
        record = parse_json_lines(cap_json_logs)[-1]
        assert record["event"].startswith("Pool metrics not available")
        assert record["level"] == "debug"


class TestDisposeEngine:
    async def test_disposes_unconnected_engine(self, valid_database_url: str) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        await dispose_engine(engine)

    async def test_requires_an_engine(self) -> None:
        with pytest.raises(AssertionError):
            await dispose_engine(cast(AsyncEngine, None))

    async def test_suppresses_disposal_errors(self, cap_json_logs: io.StringIO) -> None:
        await dispose_engine(cast(AsyncEngine, _EngineWithFailingDispose()))
        errors = assert_log_event_count(
            cap_json_logs, "Error occurred during database engine disposal"
        )
        record = errors[0]
        assert record["level"] == "error"
        assert record["exception"][0]["exc_type"] == "SQLAlchemyError"
        assert record["exception"][0]["exc_value"] == "dispose failed"

    async def test_logs_success_when_verbose(
        self, cap_json_logs: io.StringIO, valid_database_url: str
    ) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        await dispose_engine(engine, verbose=True)
        assert_log_event_count(cap_json_logs, "disposed successfully")


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
        for name, value in DEFAULT_ASYNC_SESSION_PARAMS.items():
            assert factory.kw[name] == value

    def test_overrides_session_defaults(self, valid_database_url: str) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        factory = create_sessionmaker(engine, expire_on_commit=True)
        assert factory.kw["expire_on_commit"] is True

    def test_requires_an_engine(self) -> None:
        with pytest.raises(AssertionError):
            create_sessionmaker(cast(AsyncEngine, None))

    def test_logs_when_verbose(
        self, cap_json_logs: io.StringIO, valid_database_url: str
    ) -> None:
        engine = create_engine(valid_database_url)
        assert engine is not None
        create_sessionmaker(engine, verbose=True)
        assert_log_event_count(cap_json_logs, "Created new session factory")


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

    async def test_reraises_sqlalchemy_error_by_default(
        self, make_fake_sessionmaker: Callable[[], FakeSessionMaker]
    ) -> None:
        fake = make_fake_sessionmaker()
        with pytest.raises(SQLAlchemyError):
            async with create_session(cast(SessionMakerT, fake)):
                raise SQLAlchemyError("boom")
        assert fake.session.transaction.exit_exc_type is SQLAlchemyError
        assert fake.session.closed is True

    async def test_swallows_sqlalchemy_error_when_not_raising(
        self, make_fake_sessionmaker: Callable[[], FakeSessionMaker]
    ) -> None:
        fake = make_fake_sessionmaker()
        async with create_session(cast(SessionMakerT, fake), raise_on_exc=False):
            raise SQLAlchemyError("boom")
        assert fake.session.transaction.exit_exc_type is SQLAlchemyError
        assert fake.session.closed is True

    async def test_reraises_unexpected_error_by_default(
        self, make_fake_sessionmaker: Callable[[], FakeSessionMaker]
    ) -> None:
        fake = make_fake_sessionmaker()
        with pytest.raises(RuntimeError):
            async with create_session(cast(SessionMakerT, fake)):
                raise RuntimeError("boom")
        assert fake.session.transaction.exit_exc_type is RuntimeError
        assert fake.session.closed is True

    async def test_swallows_unexpected_error_when_not_raising(
        self, make_fake_sessionmaker: Callable[[], FakeSessionMaker]
    ) -> None:
        fake = make_fake_sessionmaker()
        async with create_session(cast(SessionMakerT, fake), raise_on_exc=False):
            raise RuntimeError("boom")
        assert fake.session.transaction.exit_exc_type is RuntimeError
        assert fake.session.closed is True

    async def test_reraises_task_cancellation_even_when_not_raising(
        self, make_fake_sessionmaker: Callable[[], FakeSessionMaker]
    ) -> None:
        fake = make_fake_sessionmaker()
        with pytest.raises(asyncio.CancelledError):
            async with create_session(cast(SessionMakerT, fake), raise_on_exc=False):
                raise asyncio.CancelledError
        assert fake.session.transaction.exit_exc_type is asyncio.CancelledError
        assert fake.session.closed is True

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
        records = parse_json_lines(cap_json_logs)
        events = [record["event"] for record in records]
        assert "Created new database session" in events
        assert "Began transaction" in events
        assert "Transaction committed" in events
        assert any(
            record.get("extra", {}).get("context") == "job-42" for record in records
        )


class TestPublicApi:
    def test_dunder_all_lists_public_helpers(self) -> None:
        assert set(database.__all__) == {
            "SessionMakerT",
            "DEFAULT_ASYNC_ENGINE_PARAMS",
            "DEFAULT_ASYNC_SESSION_PARAMS",
            "create_engine",
            "dispose_engine",
            "create_sessionmaker",
            "create_session",
        }

    @pytest.mark.parametrize(
        "name",
        ["create_engine", "dispose_engine", "create_sessionmaker", "create_session"],
    )
    def test_exports_callable_helpers(self, name: str) -> None:
        assert callable(getattr(database, name))

    def test_exposes_session_maker_type_alias(self) -> None:
        assert get_origin(SessionMakerT) is async_sessionmaker
