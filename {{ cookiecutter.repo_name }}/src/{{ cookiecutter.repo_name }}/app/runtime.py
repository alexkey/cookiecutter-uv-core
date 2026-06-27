from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, TypedDict

from {{ cookiecutter.repo_name }} import get_settings
from {{ cookiecutter.repo_name }}.app.db.database import (
    create_engine,
    create_sessionmaker,
    dispose_engine,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from {{ cookiecutter.repo_name }}.app.db.database import SessionMakerT

__all__ = [
    "EXIT_SUCCESS",
    "EXIT_GENERAL_ERROR",
    "AppState",
    "app_lifespan",
]


EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1


class AppState(TypedDict, total=True):
    session_maker: SessionMakerT


@asynccontextmanager
async def app_lifespan() -> AsyncGenerator[AppState, None]:
    """Yields the shared application state for the duration of a command."""
    settings = get_settings()
    _verbose = settings.LOG_VERBOSE

    async_engine = create_engine(settings.DATABASE_URL, verbose=_verbose)
    if not async_engine:
        sys.exit(EXIT_GENERAL_ERROR)

    sessionmaker = create_sessionmaker(async_engine, verbose=_verbose)

    app_state: AppState = {
        "session_maker": sessionmaker,
    }
    try:
        yield app_state
    finally:
        await dispose_engine(async_engine, verbose=_verbose)
