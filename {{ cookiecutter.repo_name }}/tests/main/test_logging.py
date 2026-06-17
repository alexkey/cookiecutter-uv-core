from __future__ import annotations

import io
import json
import logging
import sys
from collections.abc import Callable, Iterator
from typing import TextIO, cast, get_args
from unittest.mock import Mock

import pytest
import structlog

from {{ cookiecutter.repo_name }} import logging as app_logging
from {{ cookiecutter.repo_name }}.logging import (
    _HANDLER_NAME,
    LOG_LEVELS,
    LogFormatT,
    LoggerT,
    OrderedKeysProcessor,
    _should_use_colors,
    check_log_level,
    get_logger,
    is_level_enabled,
    setup_logging,
)
from tests.utils import parse_json_lines


def _find_app_handler() -> logging.Handler | None:
    for handler in logging.getLogger().handlers:
        if handler.get_name() == _HANDLER_NAME:
            return handler
    return None


@pytest.fixture(autouse=True)
def _reset_logging_state() -> Iterator[None]:
    """Restores process-wide logging state around every test."""
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

        # Re-add any original handler that the test removed.
        for hnd in handlers:
            if hnd not in logger.handlers:
                logger.addHandler(hnd)

        logger.setLevel(level)

        structlog.contextvars.clear_contextvars()
        structlog.reset_defaults()


class TestCheckLogLevel:
    @pytest.mark.parametrize("name", sorted(LOG_LEVELS))
    def test_accepts_known_name_case_insensitively(self, name: str) -> None:
        assert check_log_level(name) == name
        assert check_log_level(name.lower()) == name
        assert check_log_level(name.title()) == name

    @pytest.mark.parametrize("number", sorted(set(LOG_LEVELS.values())))
    def test_accepts_known_numeric_level(self, number: int) -> None:
        assert check_log_level(number) == number

    @pytest.mark.parametrize("value", [True, False])
    def test_rejects_bool(self, value: bool) -> None:
        with pytest.raises(TypeError, match="must be string or integer"):
            check_log_level(value)

    @pytest.mark.parametrize("value", ["", "trace", "verbose", "warninge", "10"])
    def test_rejects_unknown_name(self, value: str) -> None:
        with pytest.raises(ValueError, match="invalid log level"):
            check_log_level(value)

    @pytest.mark.parametrize("value", [-1, 5, 11, 100])
    def test_rejects_unknown_number(self, value: int) -> None:
        with pytest.raises(ValueError, match="invalid log level"):
            check_log_level(value)

    @pytest.mark.parametrize("value", [None, 1.5, [], (), object()])
    def test_rejects_unsupported_type(self, value: object) -> None:
        with pytest.raises(TypeError, match="must be string or integer"):
            check_log_level(value)  # type: ignore[arg-type]


class TestIsLevelEnabled:
    def test_defaults_to_debug(self) -> None:
        logger = Mock()
        logger.isEnabledFor.return_value = True
        assert is_level_enabled(logger) is True
        logger.isEnabledFor.assert_called_once_with(logging.DEBUG)

    @pytest.mark.parametrize(
        ("level", "expected_number"),
        [
            ("debug", logging.DEBUG),
            ("INFO", logging.INFO),
            ("Warning", logging.WARNING),
            (logging.ERROR, logging.ERROR),
            (logging.CRITICAL, logging.CRITICAL),
        ],
    )
    def test_converts_level_to_number(
        self,
        level: str | int,
        expected_number: int,
    ) -> None:
        logger = Mock()
        logger.isEnabledFor.return_value = True
        is_level_enabled(logger, level=level)
        logger.isEnabledFor.assert_called_once_with(expected_number)

    def test_returns_false_when_level_not_enabled(self) -> None:
        logger = Mock()
        logger.isEnabledFor.return_value = False
        assert is_level_enabled(logger, level="info") is False

    @pytest.mark.parametrize("level", ["nope", -1, True])
    def test_rejects_invalid_level(self, level: str | int) -> None:
        logger = Mock()
        with pytest.raises((ValueError, TypeError)):
            is_level_enabled(logger, level=level)
        logger.isEnabledFor.assert_not_called()

    def test_reflects_configured_level(self) -> None:
        stream = io.StringIO()
        setup_logging("info", "json", log_stream=cast(TextIO, stream))
        logger = get_logger("svc")
        assert is_level_enabled(logger, level="debug") is False
        assert is_level_enabled(logger, level="info") is True
        assert is_level_enabled(logger, level="error") is True


class TestOrderedKeysProcessor:
    @pytest.mark.parametrize("bad_order", [["a", "b"], {"a", "b"}, "ab", None])
    def test_init_requires_tuple(self, bad_order: object) -> None:
        with pytest.raises(AssertionError):
            OrderedKeysProcessor(bad_order)  # type: ignore[arg-type]

    def test_orders_known_keys_then_appends_rest(self) -> None:
        processor = OrderedKeysProcessor(("timestamp", "level", "event"))
        event_dict = {
            "event": "hello",
            "user": "alice",
            "level": "info",
            "timestamp": "2026-01-01T00:00:00Z",
        }
        result = processor(None, "info", event_dict)
        assert list(result.items()) == [
            ("timestamp", "2026-01-01T00:00:00Z"),
            ("level", "info"),
            ("event", "hello"),
            ("user", "alice"),
        ]

    def test_skips_absent_known_keys(self) -> None:
        processor = OrderedKeysProcessor(("timestamp", "level", "event"))
        result = processor(None, "info", {"event": "hi", "level": "warning"})
        assert list(result) == ["level", "event"]

    def test_preserves_relative_order_of_extra_keys(self) -> None:
        processor = OrderedKeysProcessor(("level",))
        result = processor(None, "info", {"b": 2, "level": "info", "a": 1})
        assert list(result) == ["level", "b", "a"]

    def test_returns_a_new_mapping(self) -> None:
        processor = OrderedKeysProcessor(("level",))
        source = {"level": "info", "event": "x"}
        result = processor(None, "info", source)
        assert result is not source
        assert source == {"level": "info", "event": "x"}

    def test_empty_order_keeps_input_order(self) -> None:
        processor = OrderedKeysProcessor(())
        result = processor(None, "info", {"b": 1, "a": 2})
        assert list(result) == ["b", "a"]


class TestShouldUseColors:
    def test_disabled_when_no_color_is_set(
        self,
        monkeypatch: pytest.MonkeyPatch,
        make_fake_stream: Callable[..., TextIO],
    ) -> None:
        monkeypatch.setenv("NO_COLOR", "1")
        stream = make_fake_stream(isatty=True)
        assert _should_use_colors(stream, enable_colors=True) is False

    def test_disabled_when_no_color_is_empty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        make_fake_stream: Callable[..., TextIO],
    ) -> None:
        monkeypatch.setenv("NO_COLOR", "")
        stream = make_fake_stream(isatty=True)
        assert _should_use_colors(stream, enable_colors=True) is False

    def test_disabled_when_colors_not_requested(
        self,
        monkeypatch: pytest.MonkeyPatch,
        make_fake_stream: Callable[..., TextIO],
    ) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        stream = make_fake_stream(isatty=True)
        assert _should_use_colors(stream, enable_colors=False) is False

    def test_disabled_when_stream_lacks_isatty(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        stream = object()
        assert _should_use_colors(cast(TextIO, stream), enable_colors=True) is False

    def test_disabled_when_stream_is_not_a_tty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        make_fake_stream: Callable[..., TextIO],
    ) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        stream = make_fake_stream(isatty=False)
        assert _should_use_colors(stream, enable_colors=True) is False

    def test_enabled_for_requested_tty(
        self,
        monkeypatch: pytest.MonkeyPatch,
        make_fake_stream: Callable[..., TextIO],
    ) -> None:
        monkeypatch.delenv("NO_COLOR", raising=False)
        stream = make_fake_stream(isatty=True)
        assert _should_use_colors(stream, enable_colors=True) is True


class TestSetupLogging:
    def test_installs_single_named_handler_on_root(self) -> None:
        stream = io.StringIO()
        setup_logging("info", "console", log_stream=cast(TextIO, stream))
        root = logging.getLogger()
        named = [h for h in root.handlers if h.get_name() == _HANDLER_NAME]
        assert len(named) == 1
        handler = named[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.level == logging.INFO
        assert handler.stream is stream
        assert root.level == logging.INFO

    def test_defaults_stream_to_stdout(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fake_stdout = io.StringIO()
        monkeypatch.setattr(sys, "stdout", fake_stdout)
        setup_logging("debug", "console")
        handler = _find_app_handler()
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream is fake_stdout

    def test_json_format_emits_structured_record(self) -> None:
        stream = io.StringIO()
        setup_logging("debug", "json", log_stream=cast(TextIO, stream))
        get_logger("svc").info("started", user_id=7)
        records = parse_json_lines(stream)
        assert len(records) == 1
        record = records[0]
        assert record["event"] == "started"
        assert record["level"] == "info"
        assert record["logger"] == "svc"
        assert record["user_id"] == 7
        assert "timestamp" in record
        for key in ("process", "thread", "filename", "func_name", "lineno"):
            assert key in record

    def test_json_format_orders_leading_keys(self) -> None:
        stream = io.StringIO()
        setup_logging("debug", "json", log_stream=cast(TextIO, stream))
        get_logger("svc").warning("careful", detail="x")
        record = parse_json_lines(stream)[0]
        assert list(record)[:4] == ["timestamp", "logger", "level", "event"]

    def test_console_format_is_human_readable(self) -> None:
        stream = io.StringIO()
        setup_logging("debug", "console", log_stream=cast(TextIO, stream))
        get_logger("svc").info("hello world")
        output = stream.getvalue()
        assert "hello world" in output
        assert "info" in output.lower()
        with pytest.raises(json.JSONDecodeError):
            json.loads(output)

    def test_console_format_has_no_ansi_for_non_tty(self) -> None:
        stream = io.StringIO()
        setup_logging(
            "debug",
            "console",
            log_stream=cast(TextIO, stream),
            enable_colors=True,
        )
        get_logger("svc").info("plain")
        assert "\x1b[" not in stream.getvalue()

    def test_respects_configured_level(self) -> None:
        stream = io.StringIO()
        setup_logging("warning", "json", log_stream=cast(TextIO, stream))
        logger = get_logger("svc")
        logger.debug("dropped")
        logger.info("also dropped")
        logger.warning("kept")
        records = parse_json_lines(stream)
        assert [record["event"] for record in records] == ["kept"]

    def test_formats_foreign_stdlib_records(self) -> None:
        stream = io.StringIO()
        setup_logging("debug", "json", log_stream=cast(TextIO, stream))
        logging.getLogger("third_party").warning("from stdlib")
        record = parse_json_lines(stream)[0]
        assert record["event"] == "from stdlib"
        assert record["level"] == "warning"
        assert record["logger"] == "third_party"

    def test_cache_logger_on_first_use_still_logs(self) -> None:
        stream = io.StringIO()
        setup_logging(
            "debug",
            "json",
            log_stream=cast(TextIO, stream),
            cache_logger_on_first_use=True,
        )
        get_logger("svc").info("cached")
        assert parse_json_lines(stream)[0]["event"] == "cached"

    @pytest.mark.parametrize("bad_level", ["nope", -1, True])
    def test_rejects_invalid_level(self, bad_level: str | int) -> None:
        with pytest.raises((ValueError, TypeError)):
            setup_logging(bad_level, "json")  # type: ignore[arg-type]

    def test_rejects_invalid_format(self) -> None:
        stream = io.StringIO()
        with pytest.raises(ValueError, match="invalid log format"):
            setup_logging(
                "info",
                cast(LogFormatT, "bogus"),
                log_stream=cast(TextIO, stream),
            )

    def test_reconfiguration_replaces_handler(self) -> None:
        stream = io.StringIO()
        setup_logging("debug", "json", log_stream=cast(TextIO, stream))
        first = _find_app_handler()
        setup_logging("error", "json", log_stream=cast(TextIO, stream))
        root = logging.getLogger()
        named = [h for h in root.handlers if h.get_name() == _HANDLER_NAME]
        assert len(named) == 1
        assert named[0] is not first
        assert named[0].level == logging.ERROR
        assert root.level == logging.ERROR

    def test_preserves_foreign_handlers_by_default(self) -> None:
        root = logging.getLogger()
        sentinel = logging.NullHandler()
        root.addHandler(sentinel)
        stream = io.StringIO()
        setup_logging("info", "json", log_stream=cast(TextIO, stream))
        assert sentinel in root.handlers

    def test_force_remove_handlers_clears_existing(self) -> None:
        root = logging.getLogger()
        sentinel = logging.NullHandler()
        root.addHandler(sentinel)
        stream = io.StringIO()
        setup_logging(
            "info",
            "json",
            log_stream=cast(TextIO, stream),
            force_remove_handlers=True,
        )
        assert sentinel not in root.handlers
        assert [h.get_name() for h in root.handlers] == [_HANDLER_NAME]


class TestGetLogger:
    def test_returns_configured_bound_logger(self) -> None:
        stream = io.StringIO()
        setup_logging("debug", "json", log_stream=cast(TextIO, stream))
        logger = get_logger("svc").bind()
        assert isinstance(logger, LoggerT)

    def test_logger_name_appears_in_output(self) -> None:
        stream = io.StringIO()
        setup_logging("debug", "json", log_stream=cast(TextIO, stream))
        get_logger("my.component").info("ping")
        record = parse_json_lines(stream)[0]
        assert record["logger"] == "my.component"


class TestPublicApi:
    def test_defines_log_format_values(self) -> None:
        assert set(get_args(LogFormatT)) == {"json", "console"}

    def test_dunder_all_lists_public_callables(self) -> None:
        assert set(app_logging.__all__) == {
            "check_log_level",
            "get_logger",
            "is_level_enabled",
            "setup_logging",
        }
        for name in app_logging.__all__:
            assert callable(getattr(app_logging, name))
