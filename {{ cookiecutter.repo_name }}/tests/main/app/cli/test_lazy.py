from __future__ import annotations

import re

import click
import pytest

from {{ cookiecutter.repo_name }}.app.cli._lazy import LazyGroup


class TestLazyGroup:
    def test_rejects_path_that_names_no_command(self) -> None:
        group = LazyGroup(lazy_subcommands={"bad": "json.dumps"})
        expected = "`json.dumps` must name `click.Command`, not <class 'function'>"
        with pytest.raises(TypeError, match=re.escape(expected)):
            group.get_command(click.Context(group), "bad")
