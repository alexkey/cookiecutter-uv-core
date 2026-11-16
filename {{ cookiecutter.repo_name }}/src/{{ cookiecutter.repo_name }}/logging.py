from __future__ import annotations

import logging
import os
import sys
from typing import Literal, Protocol, TextIO, get_args

import structlog

LOG_LEVELS: dict[str, int] = logging.getLevelNamesMapping()

LogFormatT = Literal[
    # Structured logs with ISO timestamps and ordered fields, optimized for machine
    # parsing.
    "json",
    # Human-readable logs with timestamps and optional colors.
    "console",
]

LoggerT = structlog.stdlib.BoundLogger


class SupportsLevelCheck(Protocol):
    """A logger that can report whether it is enabled for a numeric level."""

    def isEnabledFor(self, level: int, /) -> bool: ...  # pylint: disable=invalid-name


_HANDLER_NAME = "{{ cookiecutter.repo_name }}_handler"

__all__ = [
    "check_log_level",
    "get_logger",
    "is_level_enabled",
    "setup_logging",
]


def check_log_level(value: str | int) -> str | int:
    """Validates a log level name or number.

    Args:
        value: Case-insensitive level name or numeric level.

    Returns:
        The uppercased name for string input, or the integer unchanged for numeric
        input.

    Raises:
        TypeError: If `value` is a `bool` or of a type other than `str` and `int`.
        ValueError: If `value` is an unrecognized level name or number.
    """
    if isinstance(value, str):
        value = value.upper()

    match value:
        # `bool` is an `int` subclass. Without this case, `False` would pass as NOTSET.
        case bool():
            raise TypeError(
                f"log level must be a string or an integer, not {type(value)!r}"
            )

        case str() if value in LOG_LEVELS:
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
            raise ValueError(
                f"invalid log level: {value!r} (expected one of {expected})"
            )

        case _:
            raise TypeError(
                f"log level must be a string or an integer, not {type(value)!r}"
            )


def is_level_enabled(
    logger: SupportsLevelCheck,
    *,
    level: str | int = "debug",
) -> bool:
    """Reports whether `logger` is enabled for the given level.

    Args:
        logger: Logger to query.
        level: Case-insensitive level name or numeric level.
    """
    level = check_log_level(level)

    if isinstance(level, str):
        level = LOG_LEVELS[level]

    return logger.isEnabledFor(level)


class OrderedKeysProcessor:
    """A structlog processor that emits event dictionary keys in a configured order.

    The configured keys come first, in the configured order. The other keys follow in
    their original order. Place the processor before `JSONRenderer` to get a
    predictable JSON field order.
    """

    def __init__(self, key_order: tuple[str, ...]) -> None:
        assert isinstance(key_order, tuple), (
            f"`key_order` must be a tuple, not {type(key_order)!r}"
        )
        self._key_order = key_order
        self._key_set = frozenset(key_order)

    def __call__(
        self,
        logger: structlog.typing.WrappedLogger,
        method_name: str,
        event_dict: structlog.typing.EventDict,
    ) -> structlog.typing.EventDict:
        """Reorders the keys of the event dictionary.

        Returns:
            A new event dictionary. The input dictionary stays unchanged.
        """
        ordered = {k: event_dict[k] for k in self._key_order if k in event_dict}
        ordered.update((k, v) for k, v in event_dict.items() if k not in self._key_set)

        return ordered


def _should_use_colors(stream: TextIO, *, enable_colors: bool) -> bool:
    if "NO_COLOR" in os.environ:
        return False

    return enable_colors and hasattr(stream, "isatty") and stream.isatty()


def _console_renderer(
    stream: TextIO, *, enable_colors: bool, enable_rich: bool
) -> structlog.dev.ConsoleRenderer:
    """Returns the renderer for the "console" format.

    Args:
        stream: Stream that receives log output. Colors require a TTY stream.
        enable_colors: If `True`, colorize output, as `_should_use_colors()` permits.
        enable_rich: If `True`, render tracebacks with Rich. If `False`, render them in
            the plain standard-library format. Rich can take seconds to render a long
            traceback and blocks the thread that logs, which stalls an event loop.
            Database errors produce such tracebacks.
    """
    colors = _should_use_colors(stream, enable_colors=enable_colors)

    exception_formatter: structlog.typing.ExceptionRenderer
    if enable_rich:
        # Hide local variables because they can hold secrets. Set the color system
        # explicitly because this formatter does not inherit `colors`.
        exception_formatter = structlog.dev.RichTracebackFormatter(
            color_system="truecolor" if colors else None,
            show_locals=False,
        )
    else:
        exception_formatter = structlog.dev.plain_traceback

    return structlog.dev.ConsoleRenderer(
        colors=colors, exception_formatter=exception_formatter
    )


def setup_logging(
    log_level: str,
    log_format: LogFormatT,
    *,
    log_stream: TextIO | None = None,
    enable_colors: bool = False,
    force_remove_handlers: bool = False,
    cache_logger_on_first_use: bool = False,
) -> None:
    """Configures logging with structlog.

    The configured format applies to records emitted through structlog and through the
    standard library.

    Each call replaces the handler that a previous call installed. Call the function
    again to reconfigure logging.

    Args:
        log_level: Minimum level of the records to emit. Records below this level are
            dropped even when an individual logger has a more verbose level.
        log_format: Output format. "json" produces machine-readable structured logs.
            "console" produces human-readable logs.
        log_stream: Stream that receives log output. Defaults to standard output.
        enable_colors: If `True`, colorize "console" output. Colors apply only on a
            TTY. The `NO_COLOR` environment variable suppresses them.
        force_remove_handlers: If `True`, remove all existing handlers from the root
            logger before installing the new handler.
        cache_logger_on_first_use: If `True`, assemble each logger on first use and
            cache it for later calls.

    Raises:
        ValueError: If `log_level` or `log_format` is not recognized.
    """
    level = check_log_level(log_level)

    stream = sys.stdout if log_stream is None else log_stream

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        # Apply standard-library `%` formatting to the positional arguments.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Attach a stack dump to a log entry without involving an exception.
        structlog.processors.StackInfoRenderer(),
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
    processors: list[structlog.typing.Processor] = [
        structlog.stdlib.ProcessorFormatter.remove_processors_meta,
    ]

    match log_format:
        case "json":
            shared_processors.extend(
                [
                    structlog.processors.TimeStamper(fmt="iso", utc=True),
                    structlog.processors.ExceptionRenderer(
                        structlog.tracebacks.ExceptionDictTransformer(show_locals=False)
                    ),
                ]
            )
            processors.extend(
                [
                    OrderedKeysProcessor(
                        (
                            "timestamp",
                            "logger",
                            "level",
                            "event",
                            "process",
                            "thread",
                            "filename",
                            "func_name",
                            "lineno",
                        )
                    ),
                    structlog.processors.JSONRenderer(sort_keys=False),
                ]
            )

        case "console":
            shared_processors.append(
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False)
            )
            processors.append(
                _console_renderer(
                    stream,
                    enable_colors=enable_colors,
                    # Pass `False` for plain tracebacks, rendered in milliseconds.
                    enable_rich=True,
                )
            )

        case _:
            raise ValueError(
                f"invalid log format: {log_format!r} "
                f"(expected one of {', '.join(get_args(LogFormatT))})"
            )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=LoggerT,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=cache_logger_on_first_use,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # These run only on `logging` entries that do not originate within structlog.
        foreign_pre_chain=shared_processors,
        processors=processors,
    )

    logger = logging.getLogger()

    for hnd in logger.handlers[:]:
        if force_remove_handlers or hnd.get_name() == _HANDLER_NAME:
            logger.removeHandler(hnd)
            hnd.close()

    handler = logging.StreamHandler(stream)
    handler.set_name(_HANDLER_NAME)
    handler.setLevel(level)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(level)


def get_logger(name: str) -> LoggerT:
    """Returns a logger with the given name."""
    return structlog.get_logger(name)
