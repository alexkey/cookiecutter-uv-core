# {{ cookiecutter.name }}

`{{ cookiecutter.service_name }}` is a Python service. Its importable package,
`{{ cookiecutter.repo_name }}`, uses the `src` layout. uv manages the interpreter, the
virtual environment, and the lockfile, and the Makefile is the entry point for every
development task. The package provides typed settings (pydantic-settings), structured
logging (structlog), asynchronous SQLAlchemy access to PostgreSQL (asyncpg), and a
Click command-line interface. `docker/` holds the images and a Compose stack with
PostgreSQL and Redis.

How to read these instructions:

- Sections titled **Rules** are mandatory, here and in the reference files. Follow
  them unless the user overrides one explicitly for the task at hand.
- Everything else is context for making decisions. When it disagrees with the code or
  a configuration file, trust the code and correct the instructions in the same
  change.

## Rules

1. Run Python and the tools installed in the project environment, such as Pytest,
   Ruff, ty, Mypy, Pylint, and Deptry, through a `make` target, or through `uv run`
   where no target fits. Do not call `python`, `pip`, or those tools directly: the
   targets carry the project's paths and options, and they run each tool at its
   locked version. Ordinary shell commands, such as `git` and `rg`, are not covered.
2. Before reporting a code change as complete, run `make format`, `make lint`, and
   `make test`, and resolve every finding. `make lint` fails on any Pylint message.
   After changing imports or dependencies, also run `make check-deps`; the change
   must not add a finding (`.agents/docs/workflows.md` explains the findings that
   predate it). Report every check that was not run, with the reason.
3. Change dependencies only in `pyproject.toml`, then run `make requirements` and
   `make install`. Do not edit `uv.lock` by hand and do not install packages into the
   environment by any other means.
4. Do not run `make docker-clean` or `make mostlyclean` unless the user names that
   target. `docker-clean` removes every container, image, and volume on the host, not
   only this project's. `mostlyclean` deletes the virtual environment and the entire
   uv cache.
5. Treat the database URL (`{{ cookiecutter.env_prefix }}DATABASE_URL`) as a secret.
   Keep it wrapped in `SecretStr`, and never print it, log it, or quote it in an
   exception message. Do not commit `.env` or `.env.*` files.
6. Keep local variables out of logs and shared test output, because they can hold
   secrets: do not enable `show_locals` in logging, and do not pass `--showlocals`,
   `--tb=long`, or `--full-trace` to Pytest when the output leaves the machine.
7. Before working in an area listed under [Reference](#reference), read its file and
   follow its Rules section.
8. When a change alters a command, path, rule, or design decision that these
   instructions describe, update the instructions in the same change. Edit
   `AGENTS.md`, never `CLAUDE.md`, which is a symlink to it.

## Commands

| Task | Command |
| --- | --- |
| Set up a fresh checkout | `make requirements`, `make venv`, `make install` |
| List every target | `make help` |
| Format | `make format` (check only: `make check-format`) |
| Lint and type-check | `make lint` |
| Run one analysis tool | `make check-ruff`, `check-ty`, `check-mypy`, `check-pylint` |
| Check dependency declarations | `make check-deps` |
| Run the unit tests | `make test` |
| Run one test | `make test PYTEST_CUSTOM_PATH=<path under tests/main>[::Class[::test]]` |
| Run the system tests | `make autotest` (needs a database; see `.agents/docs/testing.md`) |
| Run the service | `uv run {{ cookiecutter.service_name }} run` |
| Show the CLI help | `uv run {{ cookiecutter.service_name }} --help` |

- The analysis, formatting, and test targets need the virtual environment, `uv.lock`,
  and the installed tools. When one fails with `ERROR: The virtual environment is
  missing` or `ERROR: The project lockfile does not exist`, run the setup commands.
  `make venv` fails when `.venv` already exists.
- The targets run tools with `uv run --locked`, which fails when `uv.lock` no longer
  matches `pyproject.toml`. Run `make requirements` to update the lockfile.
- `make docker-compose`, `make docker-logs`, `make docker-run`, and
  `make docker-shell` stay in the foreground or need a terminal; read
  `.agents/docs/infrastructure.md` before running them.

## Layout

```text
src/{{ cookiecutter.repo_name }}/
    __init__.py          public API: get_settings, get_logger, setup_logging
    logging.py           logging setup
    app/core/config.py   Settings and get_settings()
    app/db/database.py   engine and session helpers
    app/runtime.py       app_lifespan() and AppState
    app/cli/             Click group; commands/ holds one module per subcommand
    app/_exceptions.py   application exception hierarchy
tests/main/              unit tests, mirroring the package layout (make test)
tests/system/            tests against live services (make autotest)
tests/utils.py           shared test helpers; fixtures live in conftest.py files
docker/                  Dockerfiles, Compose file, container scripts
etc/scripts/             standalone maintenance scripts with inline dependencies
docs/exec-plans/         execution plans (active/, completed/) and the tech-debt tracker
Makefile                 every development task
pyproject.toml           metadata, dependencies, Deptry settings
ruff.toml, ty.toml, mypy.ini, pylintrc, pytest.ini    tool configuration
```

## Reference

Reference files live in `.agents/docs/`. Read a file when the task enters its area,
and skip the files the task does not need.

| File | Read it before you |
| --- | --- |
| `.agents/docs/architecture.md` | add or change a CLI command, a setting, logging, or a shared runtime resource |
| `.agents/docs/database.md` | write code that creates sessions, runs queries, or configures the engine |
| `.agents/docs/conventions.md` | write or review Python code |
| `.agents/docs/testing.md` | write, run, or debug tests |
| `.agents/docs/workflows.md` | set up the environment, change dependencies, add a Makefile target, build a distribution, or write an execution plan |
| `.agents/docs/infrastructure.md` | build an image, run the Compose stack, or change anything under `docker/` |

## Maintaining these instructions

- Each agent asset has one canonical copy, in the location that OpenAI Codex reads:
  `AGENTS.md` for these instructions, `AGENTS.override.md` for the general
  instructions, and `.agents/skills/<name>/` for each skill. Claude Code reaches them
  through the symlinks `CLAUDE.md`, `CLAUDE.local.md`, and `.claude/skills/<name>`.
  Edit only the canonical copies.
- Codex reads `AGENTS.override.md` in place of this file and reaches this file only
  through the instruction at the top of `AGENTS.override.md`. Keep that instruction.
- This file is loaded into every session. Keep it under 200 lines and limit it to
  what applies to most tasks. Put detail that serves one area into a file under
  `.agents/docs/` and list that file in the Reference table.
- Record what cannot be inferred from the code: rules, rationale, pitfalls, and where
  things belong. Point to the code or configuration file for anything it already
  states precisely, such as option lists, defaults, and versions.
- Delete an instruction when the code no longer supports it.
