# Testing

Read this before writing, running, or debugging tests. Tests run under Pytest through
two Makefile targets. For creating a test suite or reworking an existing one, the
`update-tests` skill provides a complete procedure.

## Rules

1. Put unit tests under `tests/main/`, mirroring the package layout:
   `src/{{ cookiecutter.repo_name }}/app/db/database.py` is tested by
   `tests/main/app/db/test_database.py`. Unit tests must pass without a database,
   network access, or any other running service.
2. Put tests that need a live database under `tests/system/` and mark them with
   `@pytest.mark.requires_db`.
3. Give every new test directory an `__init__.py`. The suite is a package, and helpers
   are imported as `from tests.utils import <name>`.
4. Register a new marker in `pytest_configure()` in `tests/conftest.py` before using
   it. `pytest.ini` sets `--strict-markers` and `--strict-config`, so an unregistered
   marker or an unknown option fails the run. It also sets `xfail_strict`, so an
   expected failure that passes is reported as a failure.
5. Do not add `@pytest.mark.asyncio`, and declare async fixtures with the plain
   `@pytest.fixture` decorator. pytest-asyncio runs in auto mode.
6. Build database URLs from the `database_*`, `make_database_url`, and
   `valid_database_url` fixtures instead of hard-coded strings.
7. Keep the real database password out of test output. The system-test
   `database_url` fixture is a `SecretStr`; call `get_secret_value()` only where a
   plain string is required.
8. Draw random values from the `rng` fixture, which is seeded and reproducible.

## Running tests

| Goal | Command |
| --- | --- |
| Unit tests (`tests/main`) | `make test` |
| System tests (`tests/system`) | `make autotest` |
| A subdirectory | `make test PYTEST_CUSTOM_PATH=app/db` |
| One test | `make test PYTEST_CUSTOM_PATH=app/core/test_config.py::TestGetSettings::test_returns_cached_singleton` |
| Skip slow tests | `make test PYTEST_EXTRA_OPTS=--skip-slow` |
| System tests without a database | `make autotest PYTEST_EXTRA_OPTS=--skip-db` |
| Repeat a test to expose flakiness | `make test PYTEST_CUSTOM_PATH=<test> PYTEST_EXTRA_OPTS=--count=10` |
| Reproduce a random seed | `{{ cookiecutter.env_prefix }}TEST_SEED=<seed> make test` |

- `PYTEST_CUSTOM_PATH` is relative to the target's own directory: `tests/main` for
  `make test` and `tests/system` for `make autotest`.
- `PYTEST_EXTRA_OPTS` forwards any Pytest arguments. Further variables control
  durations, live logging, and capture; `make env-show-qa` prints them with their
  current values.
- With `PYTEST_LOG_CLI=true`, log records pass through Pytest's own formatter, not the
  application's console or JSON format.
- The seed in use is printed in the test header.

### System tests

`make autotest` fails unless `{{ cookiecutter.env_prefix }}DATABASE_URL` is set and
valid and the database accepts connections. The value comes from the environment or
from `.env.local`. The Compose stack publishes PostgreSQL on `localhost:5432`; see
`infrastructure.md` for starting it and for the URL.

- Each run creates its own schema, `itest_<random>`, and drops it afterward. Tests
  create their tables inside that schema.
- `PYTEST_DEPLOYMENT` is reserved for the URL of a deployed service. The target prints
  it, and the shipped tests do not read it.
- `PYTEST_EXPORTS` in the Makefile holds shell commands that `make autotest` runs
  before Pytest, such as `export` statements.

## Fixtures and helpers

A fixture applies to every test at or below the directory of its `conftest.py`. The
`conftest.py` files and `tests/utils.py` are authoritative; this list tells you where
to look.

| Location | Provides |
| --- | --- |
| `tests/conftest.py` | The `slow` and `requires_db` markers, the `--skip-slow` and `--skip-db` options, and `rng` |
| `tests/main/conftest.py` | `reset_logging_state` (automatic), `cap_json_logs`, `make_fake_stream`, and the database URL fixtures |
| `tests/main/app/db/conftest.py` | `make_fake_sessionmaker`, with fake session and transaction objects |
| `tests/system/conftest.py` | `app_logging` (automatic), `database_url`, `database_schema`, `database_engine`, `database_sessionmaker`, `items_table` |
| `tests/utils.py` | `fail_without_traceback`, `parse_json_lines`, `assert_log_event`, `assert_log_exception` |

- **Logging state.** `reset_logging_state` restores process-wide logging after every
  unit test, so a test may call `setup_logging()` freely.
- **Log assertions.** Request `cap_json_logs` and assert on the captured stream with
  `assert_log_event(stream, match, count=1, **fields)` or
  `assert_log_exception(stream, match, exc_type)`. Prefer them to indexing parsed
  records by hand; `assert_log_exception` searches the whole exception chain.
- **Sessions without a database.** Pass an instance of the class that
  `make_fake_sessionmaker` returns to `create_session()`, then inspect its `session`
  and `session.transaction` to assert commit or rollback.
- **Unmet prerequisites.** Call `fail_without_traceback(reason)` when an external
  prerequisite is missing; a traceback adds nothing there.
- **Settings isolation.** A test that builds `Settings` or calls `get_settings()` must
  not see the developer's environment, `.env.local`, or a cached instance. Follow the
  `_isolate_settings` and `valid_environment` fixtures in
  `tests/main/app/core/test_config.py`. When a second module needs a fixture, move it
  to the nearest shared `conftest.py`; Pylint reports a copied block as
  `duplicate-code`.

## Conventions

- Group the tests of one function or class in a `Test<Subject>` class, and name each
  test after the behavior it checks: `test_rolls_back_and_reraises_by_default`.
- Give parametrized cases readable identifiers with `pytest.param(..., id="...")`.
- Name a fixture that returns a factory `make_<thing>`.
- Use the `slow` marker for expensive tests; `--skip-slow` skips them.
