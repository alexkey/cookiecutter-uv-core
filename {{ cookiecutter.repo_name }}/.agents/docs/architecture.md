# Architecture

Read this before adding or changing a CLI command, a setting, logging behavior, or a
resource shared across the application. `database.md` covers database access.

Paths are relative to `src/{{ cookiecutter.repo_name }}/` unless they start with a
top-level directory such as `tests/` or `docker/`.

## Rules

1. Register every subcommand in `_SUBCOMMANDS` in `app/cli/__init__.py`, keyed by the
   command name and mapped to the dotted path of its `click.Command`. Do not import a
   command module from `app/cli/__init__.py`.
2. Keep the modules on the CLI's startup path cheap to import. These are the package
   root `__init__.py`, `app/__init__.py`, and every module under `app/cli/`. Each
   command module belongs to the startup path, because the group's `--help` imports it
   to show the command's short help. In these modules, import with `lazy` every name
   that only function bodies use. Use a regular import only for a cheap import of a
   name that the module uses while it loads, such as a decorator. Make no call into
   settings, logging, or the database at module level.
   `tests/main/app/cli/test_cli.py` fails when `--help` or `--version` loads a
   third-party package other than Click.
3. Stack the command decorators directly below `@click.command` in this order:
   `@configure`, `@announce`, `@run_async`.
4. Acquire shared resources only through `app_lifespan()`. Do not create or dispose
   the database engine or the session factory in a command.
5. Define settings only as fields of `Settings` in `app/core/config.py`, and read them
   only through `get_settings()`. Do not read `{{ cookiecutter.env_prefix }}*`
   environment variables directly in application code.
6. Create loggers with `get_logger(__name__)`, and configure logging only through
   `setup_logging()`.

## Components

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Public API: lazily re-exports `get_settings`, `get_logger`, `is_level_enabled`, `setup_logging` |
| `__main__.py` | `python -m {{ cookiecutter.repo_name }}`; calls `main()` |
| `logging.py` | structlog configuration shared by structlog and standard-library loggers |
| `app/__init__.py` | `__project_name__` and `__version__`, read from the installed distribution metadata |
| `app/core/config.py` | `Settings` model and the cached `get_settings()` accessor |
| `app/db/database.py` | Engine, session factory, and transactional session helpers |
| `app/runtime.py` | `app_lifespan()`, `AppState`, and the process exit codes |
| `app/cli/__init__.py` | Click group `cli`, `main()`, and the `_SUBCOMMANDS` registry |
| `app/cli/_lazy.py` | `LazyGroup`, which imports a subcommand only when it is resolved |
| `app/cli/_decorators.py` | `configure`, `announce`, `run_async` |
| `app/cli/commands/` | One module per subcommand |
| `app/_exceptions.py` | Application-layer exception hierarchy; empty in the generated project |

`app/__init__.py` requires the installed distribution
`{{ cookiecutter.service_name }}`, which `make install` provides. The version comes
from `[project].version` in `pyproject.toml`.

## Startup flow

1. The console script `{{ cookiecutter.service_name }}` and
   `python -m {{ cookiecutter.repo_name }}` both call `main()`, which runs the Click
   group `cli`. `[project.scripts]` in `pyproject.toml` declares the console script.
2. `LazyGroup` resolves the subcommand name through `_SUBCOMMANDS` and imports only
   that command's module.
3. `configure` resolves the settings and configures logging. Logging therefore uses
   the effective configuration from the first record.
4. `announce` logs the settings at debug level and a version banner at info level.
5. `run_async` drives the `async def` command body with `asyncio.run()`.
6. The body enters `app_lifespan()`, which creates the database engine and the session
   factory and yields them in an `AppState`. On exit, the lifespan disposes the engine
   whether the body returned or raised.

The shipped `run` command is a stub: it enters the lifespan and does nothing else.
The service's own behavior goes into it or into further subcommands.

## Design decisions

- **Lazy subcommands and lazy imports.** `LazyGroup` imports a command's module only
  when the command is resolved. As a result, running one command never imports
  another. The group's `--help` resolves every command, because Click reads each
  short help from the command object. Explicit lazy imports keep that cheap. PEP 810
  added them in Python 3.15: a `lazy` import binds the name at once and loads the
  module on first use. A command's dependencies therefore load only when its body
  runs, and `--help` and `--version` load nothing beyond the standard library and
  Click. A broken lazy import fails at first use, not at import.
  `tests/main/app/cli/test_cli.py` imports every module with lazy imports disabled to
  catch it. A registered path that does not name a `click.Command` raises `TypeError`
  when the command is resolved.
- **The lifespan owns shared resources.** The database layer requires that the engine
  and the session factory are created once and disposed once. The lifespan enforces
  this for every command. Further shared resources extend `AppState`.
- **Fail fast at startup.** The lifespan exits with `EXIT_GENERAL_ERROR` when the
  engine cannot be created, instead of yielding a partially initialized state.
- **Settings are a cached singleton.** `get_settings()` builds `Settings` once.
  `get_settings(reload=True)` rebuilds it from the current environment.
- **Secrets stay masked.** The database URL is a `SecretStr`, and validation errors
  hide their input through `hide_input_in_errors`. Validator messages never quote the
  URL, and rendered tracebacks omit local variables.

## Configuration

- Each field of `Settings` reads the environment variable named
  `{{ cookiecutter.env_prefix }}<FIELD>`. Names are case-sensitive. Environment
  variables that match no field are ignored.
- Values also come from an environment file: `.env.local` in the working directory by
  default, or the path in `{{ cookiecutter.env_prefix }}ENV_FILE`. Process environment
  variables take precedence over the file. An entry in the file that matches no field
  is rejected. Git ignores `.env.local`.
- An empty value is read as an empty string. It does not fall back to the field
  default.
- `get_settings()` raises `pydantic.ValidationError` when a required setting is
  missing or a value is invalid.
- `DATABASE_URL` is required. It must use the `postgresql+asyncpg` driver and include
  a database name and either a host or a `host` query parameter that names a socket
  directory.
- The fields of `Settings` are the authoritative list of settings.

## Logging

- `setup_logging(log_level, log_format, ...)` applies one format to records from
  structlog and from the standard library. Each call replaces the handler that the
  previous call installed. Commands receive this configuration through `@configure`.
  Call `setup_logging()` once before logging in any other entry point.
- `log_format` is `console` or `json`. `console` output is human-readable. `json`
  output has one object per line, UTC timestamps, and a fixed order for the leading
  keys. Colors apply to `console` output on a TTY only and are suppressed when
  `NO_COLOR` is set.
- Reserve `console` for interactive use, and select `json` in real environments, such
  as a deployed service. Console rendering is synchronous and runs on the thread that
  logs. A Rich traceback of a database error takes about 2 s, and an event loop on
  that thread serves nothing in that time. Pass `enable_rich=False` to
  `_console_renderer()` in `setup_logging()` to render plain tracebacks, which take
  milliseconds.
- Define `logger = get_logger(__name__)` at module level. The modules on the CLI's
  startup path are the exception: rule 2 requires them to create the logger inside the
  function that logs. Messages accept `%`-style positional arguments. Pass context as
  keyword arguments.
- Guard expensive log preparation with `is_level_enabled(logger)`, which checks the
  debug level by default.

## Recipes

### Add a subcommand

1. Create `app/cli/commands/<name>.py` that exposes a `click.Command`, following
   `app/cli/commands/run.py`. Import with `lazy` what only the body uses, as rule 2
   requires:

   ```python
   import click

   from {{ cookiecutter.repo_name }}.app.cli._decorators import (
       announce,
       configure,
       run_async,
   )
   lazy from {{ cookiecutter.repo_name }}.app.runtime import app_lifespan


   @click.command("healthcheck", help="Verify the database connection.")
   @configure
   @announce
   @run_async
   async def healthcheck_cmd() -> None:
       async with app_lifespan() as app_state:
           session_maker = app_state["session_maker"]
           ...
   ```

2. Add one entry to `_SUBCOMMANDS` in `app/cli/__init__.py`:
   `"healthcheck": "{{ cookiecutter.repo_name }}.app.cli.commands.healthcheck.healthcheck_cmd"`.
3. Confirm the registration with
   `uv run {{ cookiecutter.service_name }} healthcheck --help`. Then run `make test`,
   which fails when the new module makes `--help` load a third-party package.

### Add a setting

1. Add a field to `Settings` with `Field(<default>, description=...)`. Use `...` as
   the default of a required setting.
2. Validate with an `Annotated[..., AfterValidator(...)]` alias, as `LogLevel` and
   `DatabaseURL` do. Type a secret as `SecretStr`, and keep its value out of the
   validator's error messages.
3. Give the variable a value under `environment:` in `docker/docker-compose.yml` when
   the container needs one.

The automatic `_isolate_settings` fixture in `tests/main/conftest.py` derives the
variable names from the fields of `Settings` and removes them around every unit test.
A new setting therefore needs no change to the test fixtures.

### Add a resource owned by the lifespan

1. Add a key to the `AppState` typed mapping and describe it in the class docstring.
2. Create the resource in `app_lifespan()` before the `yield`, and release it in the
   `finally` block.
3. Read it in command bodies from the yielded state, as the `run` command reads
   `session_maker`.
