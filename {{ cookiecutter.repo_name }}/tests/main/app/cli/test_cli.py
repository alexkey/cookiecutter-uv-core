from __future__ import annotations

import json
import subprocess
import sys

import pytest

_PACKAGE = "{{ cookiecutter.repo_name }}"

# Runs the CLI with the arguments that follow and prints, as the last line of its
# output, the top-level names of the modules outside the standard library that the run
# loaded. Modules loaded at interpreter startup, such as those that a `.pth` file
# imports, do not count: the CLI does not control them.
_STARTUP_PROBE = """
import json
import sys


def top_level_names():
    return {name.partition(".")[0] for name in sys.modules}


preloaded = top_level_names()

from {{ cookiecutter.repo_name }}.app.cli import cli

try:
    cli.main(sys.argv[1:], prog_name="probe")
except SystemExit:
    pass

loaded = top_level_names() - preloaded - sys.stdlib_module_names

print(json.dumps(sorted(loaded)))
"""

# Imports every module of the package with lazy imports disabled, which surfaces a lazy
# import of a missing module or name here rather than at its first use.
_EAGER_IMPORT_PROBE = """
import importlib
import pkgutil
import sys

sys.set_lazy_imports_filter(lambda *args: False)

import {{ cookiecutter.repo_name }} as package

for module in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
    importlib.import_module(module.name)
"""


def _run_python(code: str, *args: str) -> subprocess.CompletedProcess[str]:
    """Runs `code` in a fresh interpreter.

    The test process has already imported the modules that the probes check for; only a
    new interpreter shows what a CLI invocation loads. `-I` ignores `PYTHON*`
    environment variables, such as `PYTHON_LAZY_IMPORTS`, that change how lazy imports
    behave.
    """
    return subprocess.run(
        [sys.executable, "-I", "-c", code, *args],
        capture_output=True,
        check=False,
        text=True,
        timeout=60,
    )


class TestCliStartup:
    @pytest.mark.parametrize(
        "args",
        [
            pytest.param(["--help"], id="help"),
            pytest.param(["--version"], id="version"),
        ],
    )
    def test_loads_no_third_party_package_except_click(self, args: list[str]) -> None:
        result = _run_python(_STARTUP_PROBE, *args)

        assert result.returncode == 0, result.stderr
        unexpected = set(json.loads(result.stdout.splitlines()[-1])) - {
            "click",
            _PACKAGE,
        }
        assert not unexpected, (
            f"{' '.join(args)} loaded {sorted(unexpected)}; "
            "a module on the startup path imports them without `lazy`"
        )

    def test_every_lazy_import_resolves(self) -> None:
        result = _run_python(_EAGER_IMPORT_PROBE)

        assert result.returncode == 0, result.stderr
