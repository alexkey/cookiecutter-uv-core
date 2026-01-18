from __future__ import annotations

import logging
import sys
from typing import Literal, get_args

import structlog
from structlog._config import BoundLoggerLazyProxy

LOG_LEVELS: dict[str, int] = logging.getLevelNamesMapping()

LogFormatT = Literal[
    # Structured logs with ISO timestamps and ordered fields, optimized for machine
    # parsing.
    "json",
    # Human-readable logs with timestamps and optional colors.
    "console",
]

LoggerT = structlog.stdlib.BoundLogger

__all__ = [
    "check_log_level",
    "is_level_enabled",
    "setup_logging",
    "get_logger",
]


def check_log_level(value: str | int) -> str | int:
    match value:
        case str() if value.upper() in LOG_LEVELS:
            return value

        case int() if value in LOG_LEVELS.values():
            return value

        case str():
            expected = ", ".join(LOG_LEVELS)
            raise ValueError(
                f"invalid log level: {value!r} (expected one of {expected})"
            )

        case int():
            expected = ", ".join(map(str, sorted(LOG_LEVELS.values())))
            raise ValueError(f"invalid log level: {value} (expected one of {expected})")

        case _:
            raise TypeError(f"keys must be string or integer, not {type(value)!r}")


def is_level_enabled(
    logger: LoggerT,
    *,
    level: str | int = "debug",
) -> bool | None:
    assert isinstance(logger, (BoundLoggerLazyProxy, LoggerT)), (
        f"logger must be {LoggerT!r}, not {type(logger)!r}"
    )
    check_log_level(level)

    if isinstance(level, str):
        level = LOG_LEVELS[level.upper()]

    return logger.isEnabledFor(level)


class OrderedKeysProcessor:
    """A structlog processor that reorders event dictionary keys according to a
    specified order.

    This processor ensures that when using JSONRenderer, the output JSON will have keys
    in a predictable order, with specified keys appearing first (if present) and any
    additional keys appended at the end.
    """

    def __init__(self, key_order: list[str]) -> None:
        """Initializes the processor with the desired key order."""
        assert isinstance(key_order, list), (
            f"key_order must be a list, got {type(key_order)!r}"
        )
        self._key_order = key_order

    def __call__(
        self,
        logger: structlog.typing.WrappedLogger,
        method_name: str,
        event_dict: structlog.typing.EventDict,
    ) -> structlog.typing.EventDict:
        """Processes the event dictionary to reorder keys according to the specified
        order.

        Returns:
            A new dictionary with keys reordered according to `self._key_order`.
        """
        keys = set(self._key_order)

        ordered = {k: event_dict[k] for k in self._key_order if k in event_dict}
        ordered.update((k, v) for k, v in event_dict.items() if k not in keys)

        return ordered


def setup_logging(
    log_level: str, log_format: LogFormatT, *, enable_colors: bool = False
) -> None:
    """Configures logging with structlog."""
    level = log_level.upper()
    assert level in LOG_LEVELS, (
        f"invalid log level: {level!r} (expected one of {', '.join(LOG_LEVELS)})"
    )

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=LOG_LEVELS[level],
    )

    processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        # Apply stdlib-like (%) string formatting.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Attach a stack dump to a log entry without involving an exception.
        structlog.processors.StackInfoRenderer(),
        # Decode byte string values.
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.PROCESS,
                structlog.processors.CallsiteParameter.THREAD,
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            }
        ),
    ]

    match log_format:
        case "json":
            processors.extend(
                [
                    # Replace an `exc_info` field with an exception string field using
                    # Python's built-in traceback formatting.
                    structlog.processors.format_exc_info,
                    structlog.processors.TimeStamper(fmt="iso", utc=True),
                    # FIXME(axk): Creates new dictionary on every log event:
                    OrderedKeysProcessor(
                        [
                            "timestamp",
                            "logger",
                            "level",
                            "event",
                            "process",
                            "thread",
                            "filename",
                            "func_name",
                            "lineno",
                        ]
                    ),
                    structlog.processors.JSONRenderer(indent=4, sort_keys=False),
                ]
            )

        case "console":
            processors.extend(
                [
                    structlog.processors.TimeStamper(
                        fmt="%Y-%m-%d %H:%M:%S", utc=False
                    ),
                    structlog.dev.ConsoleRenderer(colors=enable_colors),
                ]
            )

        case _:
            raise ValueError(
                f"invalid log format: {log_format!r} "
                f"(expected one of {', '.join(get_args(LogFormatT))})"
            )

    structlog.configure_once(
        processors=processors,
        wrapper_class=LoggerT,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> LoggerT:
    """Returns a logger with the given name."""
    return structlog.get_logger(name)
