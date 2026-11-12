from __future__ import annotations

import functools
from typing import TYPE_CHECKING
lazy import asyncio

lazy from {{ cookiecutter.repo_name }} import (
    get_logger,
    get_settings,
    is_level_enabled,
    setup_logging,
)
lazy from {{ cookiecutter.repo_name }}.app import (
    __project_name__,
    __version__,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing import Any

__all__ = [
    "announce",
    "configure",
    "run_async",
]


def configure[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Resolves settings and configures logging before a command body executes."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        settings = get_settings()
        setup_logging(
            log_level=settings.LOG_LEVEL,
            log_format=settings.LOG_FORMAT,
            enable_colors=settings.LOG_COLORS,
        )

        return func(*args, **kwargs)

    return wrapper


def announce[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Logs the startup announcement before a command body runs."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # Create the logger per call: CLI command resolution imports this module.
        logger = get_logger(__name__)

        settings = get_settings()
        if is_level_enabled(logger):
            logger.debug("%r", settings)

        logger.info("Welcome to %s version %s", __project_name__, __version__)

        return func(*args, **kwargs)

    return wrapper


def run_async[**P](func: Callable[P, Coroutine[Any, Any, None]]) -> Callable[P, None]:
    """Adapts an async command body into a synchronous Click callback.

    Args:
        func: Coroutine function forming the command body.

    Returns:
        A synchronous callable that drives the coroutine to completion.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> None:
        asyncio.run(func(*args, **kwargs))

    return wrapper
