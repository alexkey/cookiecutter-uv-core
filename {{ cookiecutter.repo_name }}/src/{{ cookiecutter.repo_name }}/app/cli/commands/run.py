from __future__ import annotations

import click

from {{ cookiecutter.repo_name }}.app.cli._decorators import (
    announce,
    configure,
    run_async,
)
from {{ cookiecutter.repo_name }}.app.runtime import app_lifespan

__all__ = [
    "run_cmd",
]


@click.command("run", help="Run the application.")
@configure
@announce
@run_async
async def run_cmd() -> None:
    async with app_lifespan() as app_state:
        session_maker = app_state["session_maker"]  # noqa: F841
        ...
