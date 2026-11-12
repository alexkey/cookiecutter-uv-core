from __future__ import annotations

import io
import logging
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TextIO, cast

import pytest
import structlog

from {{ cookiecutter.repo_name }}.app.core.config import Settings, _get_settings
from {{ cookiecutter.repo_name }}.logging import setup_logging
from tests.utils import (
    _DATABASE,
    _DRIVER,
    _HOST,
    _PASSWORD,
    _PORT,
    _USER,
    VALID_DATABASE_URL,
    _database_url,
)

_PREFIX = "{{ cookiecutter.env_prefix }}"

_CONFIG_ENV_VARS = (
    # pylint: disable=not-an-iterable
    *(f"{_PREFIX}{name}" for name in Settings.model_fields),
    f"{_PREFIX}ENV_FILE",
)


class _FakeStream:
    def __init__(self, *, isatty: bool) -> None:
        self._isatty = isatty

    def isatty(self) -> bool:
        return self._isatty


@pytest.fixture
def make_fake_stream() -> Callable[..., TextIO]:
    def factory(*, isatty: bool) -> TextIO:
        return cast(TextIO, _FakeStream(isatty=isatty))

    return factory


@pytest.fixture
def database_driver() -> str:
    return _DRIVER


@pytest.fixture
def database_user() -> str:
    return _USER


@pytest.fixture
def database_password() -> str:
    return _PASSWORD


@pytest.fixture
def database_host() -> str:
    return _HOST


@pytest.fixture
def database_port() -> int:
    return _PORT


@pytest.fixture
def database_name() -> str:
    return _DATABASE


@pytest.fixture
def make_database_url() -> Callable[..., str]:
    return _database_url


@pytest.fixture
def valid_database_url() -> str:
    return VALID_DATABASE_URL


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Removes config env vars and clears the cached singleton around every test."""
    for name in _CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    _get_settings.cache_clear()
    try:
        yield
    finally:
        _get_settings.cache_clear()


@pytest.fixture
def valid_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Supplies a valid database URL and an empty environment file.

    The empty file isolates the test from `.env.local`.
    """
    empty_env_file = tmp_path / ".env.empty"
    empty_env_file.write_text("", encoding="utf-8")

    monkeypatch.setenv(f"{_PREFIX}ENV_FILE", str(empty_env_file))
    monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", VALID_DATABASE_URL)


@pytest.fixture(autouse=True)
def reset_logging_state() -> Iterator[None]:
    """Isolates process-wide logging state around every test."""
    logger = logging.getLogger()
    handlers = logger.handlers[:]
    level = logger.level

    try:
        yield
    finally:
        # Remove any handler now present that was not in the original snapshot.
        for hnd in logger.handlers[:]:
            if hnd not in handlers:
                logger.removeHandler(hnd)
                hnd.close()

        # Re-add any original handler that a test removed.
        for hnd in handlers:
            if hnd not in logger.handlers:
                logger.addHandler(hnd)

        logger.setLevel(level)

        structlog.contextvars.clear_contextvars()
        structlog.reset_defaults()


@pytest.fixture
def cap_json_logs() -> Iterator[io.StringIO]:
    """Captures application logs as JSON for assertions with `parse_json_lines`.

    Yields:
        The stream receiving JSON log lines. The autouse `reset_logging_state` fixture
        removes the handler installed here during teardown.
    """
    stream = io.StringIO()
    setup_logging("debug", "json", log_stream=stream)

    yield stream
