from __future__ import annotations

from types import MappingProxyType

import click

from {{ cookiecutter.repo_name }}.app import (
    __project_name__,
    __version__,
)
from {{ cookiecutter.repo_name }}.app.cli._lazy import LazyGroup

__all__ = [
    "cli",
    "main",
]

_SUBCOMMANDS = MappingProxyType(
    {
        "run": "{{ cookiecutter.repo_name }}.app.cli.commands.run.run_cmd",
    }
)


@click.group(
    cls=LazyGroup,
    context_settings={"help_option_names": ["-h", "--help"]},
    lazy_subcommands=_SUBCOMMANDS,
)
@click.version_option(version=__version__, prog_name=__project_name__)
def cli() -> None:
    pass


def main() -> None:
    cli()
