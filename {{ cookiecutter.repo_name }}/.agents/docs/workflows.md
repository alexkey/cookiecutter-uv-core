# Development workflows

Read this before setting up the environment, changing dependencies, adding a Makefile
target, building a distribution, or writing an execution plan. The Makefile is the
authoritative list of targets and variables: `make help` lists the targets, and the
`make env-show-python`, `make env-show-qa`, and `make env-show-docker` targets print
the variables with their current values.

## Rules

1. Keep `uv.lock` consistent with `pyproject.toml`. After any change to the
   dependencies, run `make requirements` and then `make install`.
2. Follow the constraint style of the neighboring entries when declaring a
   dependency; runtime dependencies use the compatible-release operator (`~=`).
   Declare a tool that only development needs in the matching group under
   `[dependency-groups]`, not under `[project].dependencies`.
3. Precede every new Makefile target with a `# target: <name> - <description>`
   comment and a `.PHONY` declaration. `make help` builds its list from those
   comments.

Targets take their options through Makefile variables, for example
`make test PYTEST_EXTRA_OPTS=--skip-slow`.

## Environment

Required tools: GNU make, GNU sed (`gsed` on macOS), Git, uv, and Docker for the
container targets. ripgrep is optional; the Makefile uses it when present.

```sh
make requirements   # create or update uv.lock
make venv           # create .venv; fails when it already exists
make install        # sync .venv with uv.lock
```

- `make` without a target prints the package name, version, platform, and environment
  path.
- `make env-check`, `env-check-git`, `env-check-python`, `env-check-venv`,
  `env-check-lockfile`, `env-check-docker`, and `env-check-qa` verify single
  prerequisites. Most targets depend on the checks they need and stop with
  `ERROR: ...` when one fails.
- The Makefile pins the expected uv version in `UV_VERSION`. A different installed
  version produces a warning, not a failure.
- uv uses only the interpreters that it manages (`--python-preference=only-managed`),
  at the version in `.python-version`.
- `make install` syncs exactly: it removes packages that the lockfile does not list.
  `UV_SYNC_EXTRA_OPTS=--inexact` keeps them, and `INSTALL_EXTRAS="<name> ..."` or
  `UV_SYNC_EXTRA_OPTS=--all-extras` installs optional dependencies.
- `make force-install` reinstalls every package.

## Quality checks

| Target | Tool | Configuration |
| --- | --- | --- |
| `make format`, `make check-format` | Ruff formatter and import sorting | `ruff.toml` |
| `make check-ruff` | Ruff linter | `ruff.toml` |
| `make check-ty` | ty | `ty.toml` |
| `make check-mypy` | Mypy with the Pydantic plugin | `mypy.ini`, `MYPY_OPTS` |
| `make check-pylint` | Pylint | `pylintrc`, `PYLINT_OPTS` |
| `make lint` | The four analysis targets above | |
| `make check-deps` | Deptry | `[tool.deptry]` in `pyproject.toml` |
| `make test`, `make autotest` | Pytest | `pytest.ini`; see `testing.md` |

- The targets cover `src`, `tests`, and `etc/scripts`.
- Pylint runs with `fail-under=10.0`: a single message fails `make check-pylint` and
  therefore `make lint`.
- `make lint` stops at the first failing tool. Run the remaining `check-*` targets
  individually to see all findings.
- `make check-deps` reports imports without a declared dependency, declared
  dependencies that nothing imports, and imports of transitive or development-only
  packages. Record an intended exception under `[tool.deptry.per_rule_ignores]` with
  a comment that gives the reason.
- `make check-deps` fails while `pyproject.toml` declares a library that no module
  imports; Deptry reports each one as `DEP002`. The project template ships several
  such declarations. Judge a change by the findings it adds or removes, and do not
  delete or ignore a declaration only to make the target pass.

## Dependencies

Add or remove a dependency by editing `pyproject.toml`, then apply rule 1. The `dev`
group is installed by default and includes the `types`, `check`, and `test` groups.

To update the dependencies:

1. Review the current state. `make requirements-check` lists the installed packages
   and the outdated ones, transitive dependencies included. `make requirements-try`
   lists the outdated direct dependencies and previews the upgrade that the current
   constraints allow, without writing the lockfile.
2. Run `make requirements-bump`. It rewrites `pyproject.toml` only: it raises the `~=`
   and `>=` clauses of outdated direct dependencies to the latest releases and
   preserves everything else in each requirement. It reports a requirement whose
   other clauses would exclude the latest release and leaves it unchanged. The
   outdated versions come from the lockfile, so lock any pending `pyproject.toml`
   change first.
3. Run `make requirements-up` to re-resolve every package, transitive ones included,
   to the newest versions that the constraints allow and to install them. To upgrade
   only the bumped dependencies and keep the other locked versions, run
   `make requirements` and `make install` instead.
4. Run `make requirements-check` again, then the checks from the Rules section of
   `AGENTS.md`.

Other targets: `make requirements-tree` prints the dependency tree,
`make requirements-refresh` refreshes cached package data before locking, and
`make requirements UV_LOCK_EXTRA_OPTS=--upgrade-package=<name>` upgrades one package.

## Building and versioning

- `make dist` builds the source distribution and the wheel into `dist/` with the
  `uv_build` backend.
- The version is the static `[project].version` in `pyproject.toml`. The Makefile
  reads it for `PACKAGE_VERSION`, which also tags the Docker image. The lockfile
  records it, and the package reads it from the installed metadata: after changing
  it, run `make requirements` and `make install`.
- `Changelog` records the changes of each version; follow the format of the existing
  entries.

## Execution plans

An execution plan records a change that is too large for one conversation: its
requirements, design decisions, steps, validation, and progress. It is self-contained,
so a later session can continue the work from the plan and the working tree alone. For
planning and implementing such a change, the `develop` skill provides a complete
procedure: it writes the plan, keeps it current during the implementation, and closes it
when the work is done. Only the user starts the skill, by name: `/develop` in Claude
Code, `$develop` in Codex. When a task fits the skill, suggest it to the user instead of
following its procedure on your own.

- `docs/exec-plans/active/` holds the plans in progress, and
  `docs/exec-plans/completed/` the completed and cancelled ones. A plan moves from the
  first to the second when it is closed.
- `docs/exec-plans/tech-debt-tracker.md` lists deferred work, known shortcuts, and
  declined follow-ups. Each entry names its source and its remedy, and is removed in the
  change that resolves it.
- A plan's file name is its creation date in ISO 8601 form followed by a short
  kebab-case description, such as `docs/exec-plans/active/2026-11-12-report-export.md`.
  Every date and time in the plans and in the tracker is UTC. The `.gitkeep` files keep
  the empty directories under version control and are not plans.
- Plans are project files: keep them under version control with the change they
  describe.

## Source notes

`make show-notes` lists the DEBUG, FIXME, TODO, and XXX notes in the files that Git
tracks or would track, with `NOTES_CONTEXT` lines of context.
`make show-notes-recent` limits the search to the files of the last `GIT_DEPTH`
commits and to modified files. Both need a Git work tree.

## Cleaning

- `make clean` removes caches and bytecode.
- `make distclean` removes build and distribution output.
- `make mostlyclean` also deletes the virtual environment and the entire uv cache,
  which other projects share. See rule 4 in `AGENTS.md`.
