# Architecture

Read this before adding or changing a CLI command, a setting, logging behavior, or a
resource shared across the application. Database access is covered in `database.md`.

Paths are relative to `src/{{ cookiecutter.repo_name }}/` unless they start with a
top-level directory such as `tests/` or `docker/`.

## Rules

1. Register every subcommand in `_SUBCOMMANDS` in `app/cli/__init__.py`, keyed by the
   command name and mapped to the dotted path of its `click.Command`. Do not import a
   command module from `app/cli/__init__.py`: the group must answer `--help` and
   `--version` without importing any command.
2. Stack the command decorators directly below `@click.command` in this order:
   `@configure`, `@announce`, `@run_async`.
3. Acquire shared resources only through `app_lifespan()`. A command does not create
   or dispose the database engine or the session factory itself.
4. Define settings only as fields of `Settings` in `app/core/config.py`, and read them
   only through `get_settings()`. Application code does not read
   `{{ cookiecutter.env_prefix }}*` environment variables on its own.
5. Create loggers with `get_logger(__name__)`, and configure logging only through
   `setup_logging()`.

## Components

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Public API: re-exports `get_settings`, `get_logger`, `is_level_enabled`, `setup_logging` |
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
| `app/_exceptions.py` | Home of the application-layer exception hierarchy; holds no classes yet |

`app/__init__.py` needs the distribution `{{ cookiecutter.service_name }}` to be
installed, which `make install` does. The version comes from `[project].version` in
`pyproject.toml`.

## Startup flow

1. The console script `{{ cookiecutter.service_name }}` (declared under
   `[project.scripts]` in `pyproject.toml`) and
   `python -m {{ cookiecutter.repo_name }}` both call `main()`, which runs the Click
   group `cli`.
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
The service's own behavior is added to it or as further subcommands.

## Design decisions

- **Lazy subcommands.** A command pays for its imports only when it runs, and the
  group's `--help` and `--version` stay cheap. Keep heavy imports inside the command
  modules. A registered path that does not name a `click.Command` raises `TypeError`
  when the command is resolved.
- **The lifespan owns shared resources.** Creating the engine and the session factory
  once and disposing them once is a requirement of the database layer; the lifespan
  enforces it for every command. Further shared resources are added by extending
  `AppState`.
- **Fail fast at startup.** When the engine cannot be created, the lifespan exits with
  `EXIT_GENERAL_ERROR` instead of yielding a partially initialized state.
- **Settings are a cached singleton.** `get_settings()` builds `Settings` once;
  `get_settings(reload=True)` rebuilds it from the current environment.
- **Secrets stay masked.** The database URL is a `SecretStr`, validation errors hide
  their input (`hide_input_in_errors`), validator messages never quote the URL, and
  rendered tracebacks omit local variables.

## Configuration

- Each field of `Settings` reads the environment variable named
  `{{ cookiecutter.env_prefix }}<FIELD>`. Names are case-sensitive. Environment
  variables that match no field are ignored.
- Values also come from an environment file: `.env.local` in the working directory by
  default, or the path in `{{ cookiecutter.env_prefix }}ENV_FILE`. Process environment
  variables take precedence over the file. An entry in the file that matches no field
  is rejected. The file is ignored by Git.
- An empty value is read as an empty string; it does not fall back to the field
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
  previous call installed. Commands get this through `@configure`; any other entry
  point calls it once before logging.
- `log_format` is `console` (human-readable) or `json` (one object per line, UTC
  timestamps, a fixed order for the leading keys). Colors apply to `console` output
  on a TTY only and are suppressed when `NO_COLOR` is set.
- Define `logger = get_logger(__name__)` at module level. Messages accept `%`-style
  positional arguments; pass context as keyword arguments.
- Guard expensive log preparation with `is_level_enabled(logger)`, which checks the
  debug level by default.

## Recipes

### Add a subcommand

1. Create `app/cli/commands/<name>.py` that exposes a `click.Command`, following
   `app/cli/commands/run.py`:

   ```python
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
   `uv run {{ cookiecutter.service_name }} healthcheck --help`.

### Add a setting

1. Add a field to `Settings` with `Field(<default>, description=...)`; use `...` as the
   default of a required setting.
2. Validate with an `Annotated[..., AfterValidator(...)]` alias, as `LogLevel` and
   `DatabaseURL` do. Type a secret as `SecretStr`, and keep its value out of the
   validator's error messages.
3. Add the variable name to `_CONFIG_ENV_VARS` in
   `tests/main/app/core/test_config.py`. The isolation fixture there removes those
   variables, which keeps a developer's environment from leaking into the tests.
4. Give the variable a value under `environment:` in `docker/docker-compose.yml` when
   the container needs one.

### Add a resource owned by the lifespan

1. Add a key to the `AppState` typed mapping and describe it in the class docstring.
2. Create the resource in `app_lifespan()` before the `yield`, and release it in the
   `finally` block.
3. Read it in command bodies from the yielded state, as `session_maker` is read.
