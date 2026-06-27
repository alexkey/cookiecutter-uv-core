from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

import click

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

__all__ = [
    "LazyGroup",
]


class LazyGroup(click.Group):
    """A Click group that imports each subcommand only when it is resolved."""

    def __init__(
        self,
        *args: Any,
        lazy_subcommands: Mapping[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initializes the group.

        Args:
            lazy_subcommands: Map of command name to the dotted path of its
                click.Command.
        """
        super().__init__(*args, **kwargs)
        self.lazy_subcommands: dict[str, str] = dict(lazy_subcommands or {})

    def list_commands(self, ctx: click.Context) -> list[str]:
        eager = super().list_commands(ctx)
        lazy = sorted(self.lazy_subcommands)

        return [*eager, *lazy]

    def _lazy_load(self, cmd_name: str) -> click.Command:
        import_path = self.lazy_subcommands[cmd_name]
        module_name, _, object_name = import_path.rpartition(".")

        command = getattr(importlib.import_module(module_name), object_name)

        if not isinstance(command, click.Command):
            raise TypeError(
                f"{import_path!r} must be a click.Command, not {type(command)!r}"
            )

        return command

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name in self.lazy_subcommands:
            return self._lazy_load(cmd_name)

        return super().get_command(ctx, cmd_name)
