====================
cookiecutter-uv-core
====================

*cookiecutter-uv-core* is a Cookiecutter_ template for Python services managed with uv_.
It generates a typed package in the ``src`` layout with layered configuration through
*Pydantic*, structured logging through *structlog*, asynchronous *SQLAlchemy* access to
PostgreSQL, a *Click* command-line interface, and multi-platform Docker images.

A Makefile drives dependency management, containerization, code quality checks, and
tests. The generated project also carries instructions and skills for the *Claude Code*
and *OpenAI Codex* coding agents.

.. contents:: Contents
   :depth: 2
   :backlinks: none

Prerequisites
=============

Generating a project requires only *uv*, which runs Cookiecutter. Working with the
generated project requires the following tools:

* GNU make;
* GNU sed, which ``brew install gnu-sed`` installs on macOS;
* Git;
* *uv*, preferably at the version that the ``uv_version`` prompt pins;
* Docker Desktop on macOS, or Docker Engine with QEMU on Linux [#docker]_.

ripgrep is optional. The Makefile uses it when it is installed, for example through
``cargo install ripgrep``.

``make install`` installs the following tools as development dependencies of the
project:

* Deptry_;
* Ruff_;
* ty_;
* Mypy_;
* Pylint_;
* Pytest_.

.. [#docker] `Simple multi-platform build using emulation with Docker <https://docs.docker.com/build/building/multi-platform/#simple-multi-platform-build-using-emulation>`_.

**Environment**

Run the following targets in the generated project to check the tools and to inspect the
active configuration:

* Show the project version and the environment details: ``make``.

* Check the primary tools: ``make env-check``.

* Check the Git command and the work tree: ``make env-check-git``.

* Check the Python requirements:

  - the general requirements: ``make env-check-python``;
  - the project lockfile: ``make env-check-lockfile``;
  - the virtual environment: ``make env-check-venv``.

* Show the variables that configure Python and related tools: ``make env-show-python``.

* Check the Docker requirements: ``make env-check-docker``.

* Show the variables that configure Docker: ``make env-show-docker``.

* Check the requirements of the quality assurance tools: ``make env-check-qa``.

* Show the variables that configure the quality assurance tools: ``make env-show-qa``.

.. _Deptry: https://deptry.com/
.. _Ruff: https://docs.astral.sh/ruff/
.. _ty: https://docs.astral.sh/ty/
.. _Mypy: https://mypy-lang.org/
.. _Pylint: https://pylint.readthedocs.io/en/latest/
.. _Pytest: https://docs.pytest.org/en/stable/

Get Started
===========

Run Cookiecutter through ``uvx``, the tool runner of *uv*, which installs it into an
isolated environment on first use. From a local clone of this repository, run::

    uvx cookiecutter --output-dir </path/to/dir> --overwrite-if-exists .

The ``.`` names the template in the current directory. Cookiecutter creates the project
inside the directory that ``--output-dir`` names, and ``-o`` is the short form of that
option. ``--overwrite-if-exists`` permits generating into a project directory that an
earlier run created.

To generate from the GitHub repository instead, replace ``.`` with a reference of the
form ``gh:<owner>/<repo>``::

    uvx cookiecutter -o </path/to/dir> gh:alexkey/cookiecutter-uv-core

Cookiecutter prompts for the following values and shows the default of each. Press Enter
to accept a default:

* ``name`` - the project's display name, for example ``FooBar-baz``. The values
  ``service_name``, ``repo_name``, and ``env_prefix`` derive from it.
* ``version`` - the initial project version.
* ``brief`` - a one-line package summary.
* ``description`` - a longer description for the generated README.
* ``author_name`` and ``author_email`` - the author and maintainer details.
* ``url`` and ``repository`` - the URLs of the project homepage and the source
  repository.
* ``license`` - the `SPDX license identifier`_.
* ``uv_version`` and ``python_version`` - the pinned *uv* and CPython versions. The
  generated code uses explicit lazy imports and therefore requires a ``python_version``
  of 3.15 or later.
* ``docker_build_platform`` - the target platform of Docker image builds.
* ``redis_image_tag`` and ``postgres_image_tag`` - the image tags of the Docker Compose
  services.
* ``postgres_user`` - the PostgreSQL user.

Cookiecutter derives the following values from the inputs above and prompts for them as
well. Accept the derived defaults unless the project needs other values:

* ``service_name`` - the lowercased project name.
* ``repo_name`` - the importable Python package name: ``service_name`` with hyphens
  replaced by underscores.
* ``env_prefix`` - the prefix of the settings environment variables: the uppercased part
  of ``name`` before the first hyphen or underscore, followed by an underscore.
* ``python_majmin`` - the major and minor Python version.
* ``docker_compose_name`` - the Docker Compose project name.
* ``docker_prefix`` - the base path inside Docker images.
* ``year`` - the current year.

To generate a sample project with the defaults only, pass ``--no-input``::

    uvx cookiecutter -o </path/to/dir> --no-input .

The command creates the sample project ``foobar_baz``, which serves for inspection and
experiments. ``uvx cookiecutter --help`` lists every Cookiecutter option.

Change into the directory of the generated project and continue with
`A Typical Session`_. `Features`_ lists the targets of the Makefile.

.. _Cookiecutter: https://cookiecutter.readthedocs.io/
.. _uv: https://docs.astral.sh/uv/
.. _`SPDX license identifier`: https://spdx.org/licenses/

A Typical Session
-----------------

The following steps take the sample project ``foobar_baz`` from environment setup to a
running service.

Initialize a Git work tree, lock the dependencies, create the virtual environment, and
install the project::

    cd foobar_baz
    git init
    make requirements
    make venv
    make install

The ``make`` targets need no activated environment. Run any other command in the project
environment with the prefix ``uv run``, as in ``uv run foobar-baz --help``.
Alternatively, the project's ``venv`` helper activates the environment in the current
shell::

    . ./venv

Check the formatting, run the analysis tools, and run the unit tests::

    make check-format
    make lint
    make test

Build the image and start the service stack with Compose::

    make docker-build
    make docker-compose

``make docker-compose`` runs in the foreground and removes the stack, volumes included,
on exit. Run the remaining commands from a second shell while the stack runs.

Point the database URL at the PostgreSQL port that Compose publishes on ``localhost``.
Export it for the current shell::

    export FOOBAR_DATABASE_URL="postgresql+asyncpg://database:database@localhost:5432/database"

Alternatively, set the same value in the project's ``.env.local`` file, which the
settings loader reads by default.

Run the system tests against the running database::

    make autotest

Start the service, which logs its resolved configuration on startup::

    uv run foobar-baz run
    2026-06-28 16:50:46 [debug    ] Settings(LOG_LEVEL='DEBUG', LOG_FORMAT='console', LOG_COLORS=True, LOG_VERBOSE=True, DATABASE_URL=SecretStr('**********')) [foobar_baz.app.cli._decorators] filename=_decorators.py func_name=wrapper lineno=57 process=76586 thread=140704445131008
    2026-06-28 16:50:46 [info     ] Welcome to foobar-baz version 0.1.0 [foobar_baz.app.cli._decorators] filename=_decorators.py func_name=wrapper lineno=59 process=76586 thread=140704445131008
    ...

Updating the Dependencies
-------------------------

Review the current state first::

    make requirements-check
    make requirements-try

``make requirements-check`` lists the installed packages and marks the outdated ones,
transitive dependencies included. ``make requirements-try`` lists the outdated direct
dependencies and previews the upgrade that the constraints allow, without writing the
lockfile.

Raise the constraints of the outdated direct dependencies, then lock and install the
upgrade::

    make requirements-bump
    make requirements-up

``make requirements-bump`` rewrites only ``pyproject.toml``. It raises the ``~=`` and
``>=`` clauses to the latest releases and preserves the rest of each requirement as
written. It reports a requirement whose other clauses would exclude the latest release
and leaves that requirement unchanged. Lock any pending ``pyproject.toml`` change first,
because the outdated versions come from the lockfile.

``make requirements-up`` re-resolves every package, transitive dependencies included, to
the newest versions that the constraints allow, then installs them. Run
``make requirements`` and ``make install`` instead to upgrade only the bumped
dependencies and keep the other locked versions.

Confirm the result, then run the checks and tests against the upgraded packages::

    make requirements-check
    make lint
    make test

Features
========

The generated project includes a Makefile whose targets are grouped by concern.

**Managing Python**

The following targets manage the virtual environment, the dependencies, and the package
distributions:

* Create a virtual environment: ``make venv``.

* Manage the dependencies and the lockfile:

  - Update the lockfile: ``make requirements``. Set ``UV_LOCK_EXTRA_OPTS`` to
    ``--upgrade-package=<name>`` to upgrade one package.
  - Refresh all cached package data and update the lockfile:
    ``make requirements-refresh``.
  - List the outdated direct dependencies, then preview the upgrade without writing the
    lockfile: ``make requirements-try``.
  - Raise the ``~=`` and ``>=`` constraints of the outdated direct dependencies in
    ``pyproject.toml`` to their latest versions: ``make requirements-bump``. Then update
    the lockfile as `Updating the Dependencies`_ describes.
  - Re-resolve every package to the newest versions that the constraints allow, and
    install them: ``make requirements-up``.
  - List and validate the installed packages: ``make requirements-check``.
  - Display the dependency tree: ``make requirements-tree``.

* Synchronize the virtual environment with the lockfile: ``make install``. The target
  removes packages that the lockfile does not list. Set ``UV_SYNC_EXTRA_OPTS`` to:

  - ``--all-extras`` to include all optional dependencies;
  - ``--inexact`` to keep packages that the lockfile does not list.

  Set ``INSTALL_EXTRAS`` to a space-separated list of names to include selected optional
  dependencies.

* Reinstall all dependencies: ``make force-install``.

* Build the source and wheel distributions: ``make dist``.

**Managing Docker**

The following targets build images, run containers, and manage Docker resources:

* Show all images, containers, and volumes: ``make docker-info``.

* Build an image from the Dockerfile: ``make docker-build``. Set ``DOCKER_EXTRA_OPTS``
  to ``--progress=plain`` to show the full build output.

* Create and run a container from the image, removed on exit: ``make docker-run``. Set
  ``DOCKER_EXTRA_OPTS`` to ``--publish 127.0.0.1:8000:8000`` to publish the container's
  port on the host.

* Manage the service stack with Compose:

  - Start the containers in the foreground, and remove them with their volumes on exit:
    ``make docker-compose``;
  - Follow the logs from the running containers: ``make docker-logs``;
  - Open a shell in the running service container: ``make docker-shell``.

  Build the image with ``make docker-build`` before the first ``make docker-compose``,
  because the Compose file does not build it. To surface errors, warnings, and other
  problems in the log stream, filter it with ripgrep::

      make docker-logs | rg -i "(err|crit|kill|garbage|warn)"

* Remove every container and image on the host, and prune unused networks, the build
  cache, and anonymous volumes: ``make docker-clean``. The target affects all Docker
  resources on the host, not only those of the project.

**Code Quality**

The following targets list source notes, analyze dependencies, and lint, format, and
test the code:

* List the source notes with ``NOTES_CONTEXT`` lines of surrounding context. Both
  targets require a Git work tree.

  - List all notes, sorted by tag: ``make show-notes``.
  - List the notes in the files of the last ``GIT_DEPTH`` commits and in modified files:
    ``make show-notes-recent``.

* Find unused, missing, and transitive dependencies: ``make check-deps``. Configure
  *Deptry* in the ``[tool.deptry]`` section of ``pyproject.toml``. The target fails on a
  freshly generated project, because ``pyproject.toml`` declares libraries that the
  shipped code does not import, such as *FastAPI* and *Celery*. *Deptry* reports each of
  them as ``DEP002``.

* Analyze the code:

  - Lint with *Ruff*: ``make check-ruff``;
  - Perform static type checking with *ty*: ``make check-ty``;
  - Perform static type checking with *Mypy*: ``make check-mypy``;
  - Perform code analysis with *Pylint*: ``make check-pylint``;
  - Run all of the above analysis tools: ``make lint``.

  The ``MYPY_OPTS`` and ``PYLINT_OPTS`` variables and the ``ruff.toml``, ``ty.toml``,
  ``mypy.ini``, ``pytest.ini``, and ``pylintrc`` files configure the quality assurance
  tools. The analysis and formatting targets check ``src``, ``tests``, and
  ``etc/scripts``.

  The dependency, analysis, formatting, and test targets run their tools through
  ``uv run --locked``, at the versions in ``uv.lock``. They require the virtual
  environment, the lockfile, and the installed tools.

* Manage code formatting:

  - Detect unformatted files: ``make check-format``;
  - Sort imports and format all Python files: ``make format``.

* Run tests:

  - Run the unit tests in the ``PYTEST_UNIT_DIR`` subdirectory of ``tests``:
    ``make test``;
  - Run the system tests in the ``PYTEST_SYSTEM_DIR`` subdirectory of ``tests``:
    ``make autotest``.

  ``make autotest`` needs a reachable database. It fails unless
  ``{{ cookiecutter.env_prefix }}DATABASE_URL`` is set and valid, or
  ``PYTEST_EXTRA_OPTS`` passes ``--skip-db``.

  Both targets accept ``PYTEST_EXTRA_OPTS`` to forward extra *Pytest* arguments and
  ``PYTEST_CUSTOM_PATH`` to restrict the run to specific paths. `Testing`_ describes
  these and further variables.

**Auxiliary Targets**

The following targets list the targets and remove generated files:

* View all available targets: ``make help``.

* Remove the tool caches and bytecode: ``make clean``.

* Remove the build and distribution output: ``make distclean``.

* Run both cleanups, then delete the virtual environment and the entire *uv* cache,
  which other projects share: ``make mostlyclean``.

Usage
=====

The generated service rests on three runtime facilities: typed configuration, structured
logging, and asynchronous database access. An application runtime and a *Click*
command-line interface combine them into a runnable service.

Configuration (``config.py``)
-----------------------------

The typed *Pydantic* model ``Settings`` holds the runtime configuration. A cached
accessor returns it::

    from {{ cookiecutter.repo_name }} import get_settings

    settings = get_settings()

* Each setting reads the environment variable that carries its name with the project's
  prefix, for example ``{{ cookiecutter.env_prefix }}LOG_LEVEL`` and
  ``{{ cookiecutter.env_prefix }}DATABASE_URL``. Names are case-sensitive. Environment
  variables that match no setting are ignored.

* Values also come from an environment file, by default ``.env.local`` in the working
  directory. Set ``{{ cookiecutter.env_prefix }}ENV_FILE`` to load another file. Process
  environment variables take precedence over the file. An entry in the file that matches
  no setting is rejected. The generated ``.env.local`` sets every setting, and the
  fields of ``Settings`` are the authoritative list.

* ``get_settings()`` returns a cached singleton. Pass ``reload=True`` to discard the
  cache and rebuild the settings from the current environment.

* ``DATABASE_URL`` is required and validated. It must use the ``postgresql+asyncpg``
  driver and include a database name and either a host or a ``host`` query parameter
  that names a socket directory. The settings hold it as a ``SecretStr``, which stays
  masked when the settings are logged or printed.

Logging (``logging.py``)
------------------------

Logging builds on *structlog* and formats records from *structlog* and from the standard
library alike. Configure it once during startup from the settings above::

    from {{ cookiecutter.repo_name }} import get_logger, get_settings, setup_logging

    settings = get_settings()

    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        enable_colors=settings.LOG_COLORS,
    )

    logger = get_logger(__name__)
    logger.info("service started")

* Call ``setup_logging()`` once before the first log record. A later call reconfigures
  logging and replaces the handler that the previous call installed.

* ``log_format`` selects the renderer: ``console`` for human-readable output and
  ``json`` for machine-readable records, one object per line. Use ``console``
  interactively and ``json`` in deployed environments. The console renderer formats
  tracebacks with *Rich*, which can take seconds for a long traceback and blocks the
  thread that logs.

* ``log_level`` sets the threshold below which records are dropped. Level names are
  case-insensitive.

* Colors apply to ``console`` output on a TTY only and are suppressed when the
  ``NO_COLOR`` environment variable is set.

* Create module-level loggers with ``get_logger(__name__)``, and pass context as keyword
  arguments. Guard expensive log preparation with ``is_level_enabled(logger)``, which
  checks the debug level by default.

Database (``database.py``)
--------------------------

Database access uses asynchronous *SQLAlchemy* over the ``postgresql+asyncpg`` driver.
Helper functions cover the full lifecycle: creating and disposing the engine, building a
session factory, and opening sessions that commit or roll back automatically::

    from {{ cookiecutter.repo_name }} import get_settings
    from {{ cookiecutter.repo_name }}.app.db.database import (
        create_engine,
        create_session,
        create_sessionmaker,
        dispose_engine,
    )

    settings = get_settings()

    # Create the engine and session factory once during startup.
    engine = create_engine(settings.DATABASE_URL, raise_on_exc=True)
    sessionmaker = create_sessionmaker(engine)

    # Open one session per unit of work; the block is a single transaction.
    async with create_session(sessionmaker) as session:
        await session.execute(...)

    # Dispose the engine once during shutdown.
    await dispose_engine(engine)

* Create the engine once with ``create_engine()``, and reuse it for the lifetime of the
  process, because it owns the connection pool. By default, ``create_engine()`` returns
  ``None`` when creation fails. Pass ``raise_on_exc=True`` to fail fast at startup
  instead. Dispose the engine once during shutdown with ``await dispose_engine(engine)``
  to close the pooled connections.

* Build a single session factory per engine with ``create_sessionmaker()``, and share it
  as the source of every session. Do not create an engine or a factory per request or
  per task.

* ``create_session()`` is an async context manager that opens one session and wraps the
  enclosed block in a single transaction. The transaction commits when the block exits
  cleanly and rolls back on any exception. The session is always closed. Use one block
  per unit of work, and let the block own the transaction boundary. Do not call
  ``session.begin()`` or ``session.commit()`` inside it.

  - With the default ``raise_on_exc=True``, database errors and unexpected errors are
    re-raised after the rollback. ``asyncio.CancelledError`` always rolls back and
    propagates. Pass ``context=...`` to label a session in log records, and
    ``verbose=True`` to log each lifecycle step.

* **The defaults** for the engine and the sessions live in
  ``DEFAULT_ASYNC_ENGINE_PARAMS`` and ``DEFAULT_ASYNC_SESSION_PARAMS``. Read the active
  values there, and override any of them through keyword arguments to
  ``create_engine()`` and ``create_sessionmaker()``.

  - Sessions set ``expire_on_commit=False``. With the *SQLAlchemy* default of ``True``,
    ``commit()`` expires the attributes, and the first later access to each attribute
    triggers an implicit refresh SELECT. Under asyncio, that implicit I/O can run
    outside *SQLAlchemy*'s async bridge and raise ``MissingGreenlet``. The tradeoff is
    that objects are not re-fetched after a commit.

    A server-generated value from ``server_default``, ``server_onupdate``, or
    ``Computed`` is available only when *SQLAlchemy* populated it during the flush,
    typically through ``RETURNING``. A value that was not populated stays expired, and
    accessing it triggers the same implicit I/O. A value that *SQLAlchemy* does not know
    to be computed on the server can stay stale in memory. Fetch such values explicitly
    with ``await session.refresh(obj, [...])``, and load relationships eagerly with
    ``selectinload()`` instead of relying on attribute access.

  - The pool settings work together when connections pass through intermediaries.
    ``pool_pre_ping`` checks a connection when it leaves the pool and replaces one that
    was dropped while idle. ``pool_use_lifo`` keeps traffic on a small set of
    connections, which lets the surplus connections idle out on the server during quiet
    periods.

    ``pool_recycle`` limits the connection age to 1800 seconds. Keep it below the
    shortest idle timeout of any component in the network path, such as a load balancer,
    NAT, or a connection pooler. An AWS Network Load Balancer closes idle TCP
    connections after 350 seconds by default, which calls for a value such as 300
    seconds. PgBouncer closes idle client connections only when ``client_idle_timeout``
    is set, and that timeout is disabled by default. ``pool_pre_ping`` detects stale
    connections when they leave the pool, and ``pool_recycle`` keeps connections from
    reaching that state.

Application runtime and CLI
---------------------------

The service is a *Click* command-line program. An application lifespan provides the
shared resources that each command needs while it runs.

Runtime and application lifespan
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Two entry points launch the service: the console script
``{{ cookiecutter.service_name }}`` and ``python -m {{ cookiecutter.repo_name }}``. The
``[project.scripts]`` table of ``pyproject.toml`` declares the console script. Both call
``main()``, which hands control to the *Click* group ``cli``. The group parses the
arguments and dispatches to a subcommand.

The application lifespan owns the shared resources, not the individual commands.
``app_lifespan()`` is an async context manager that wraps a command body and holds the
resources for its duration:

* On entry, it creates the database engine and the session factory, and yields a shared
  ``AppState``.

* On exit, it disposes the engine whether the body returned or raised. The pooled
  connections are therefore released on every path.

* ``AppState`` is a typed mapping of the resources that the lifespan provides to the
  command body. It carries the session factory. Further resources owned by the lifespan
  extend it.

* When the engine cannot be created, the lifespan fails fast and exits with
  ``EXIT_GENERAL_ERROR`` instead of yielding a partially initialized state.

The lifespan follows the database guidance above: it creates the engine and the session
factory once and disposes them once. A command opens sessions from the supplied factory
and never manages the engine itself.

Creating commands and lazy loading
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The template ships one subcommand, ``run``, whose body is a stub. It enters the lifespan
and leaves a placeholder for the service's own logic. Further behavior goes into more
subcommands. Two mechanisms keep startup cheap:

* ``LazyGroup`` imports a subcommand's module only when that command is resolved.
  Invoking one command never imports another.

* Explicit lazy imports defer each module's dependencies until their first use. PEP 810
  added them in Python 3.15. The group's ``--help`` imports every command module to show
  its short help, but those modules load none of their dependencies until a command body
  runs. As a result, ``--help`` and ``--version`` load nothing beyond the standard
  library and *Click*.

Creating a command therefore takes two steps. First, place a module that exposes a
``click.Command`` under ``app/cli/commands/``, and import with ``lazy`` everything that
only the command body uses. For example, ``app/cli/commands/healthcheck.py`` reuses the
lifespan and the decorators below::

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

            # Open sessions from session_maker and run the check here.
            ...

Second, register the command object with one entry in the ``_SUBCOMMANDS`` mapping in
``app/cli/__init__.py``. The key is the command name, and the value is the dotted path
of the object::

    _SUBCOMMANDS = MappingProxyType(
        {
            "run": "{{ cookiecutter.repo_name }}.app.cli.commands.run.run_cmd",
            "healthcheck": "{{ cookiecutter.repo_name }}.app.cli.commands.healthcheck.healthcheck_cmd",
        }
    )

The group verifies that the entry names a ``click.Command`` when it loads the entry. The
module is imported when the group's help is shown or when
``{{ cookiecutter.service_name }} healthcheck`` runs. Its dependencies are imported only
when the command runs. A unit test fails when the group's ``--help`` or ``--version``
loads a third-party package other than *Click*. The test thereby detects an import on
the startup path that lacks the ``lazy`` keyword.

Helper decorators
^^^^^^^^^^^^^^^^^

Three decorators factor out the setup that every command shares. They stack beneath
``@click.command`` in a fixed order, as the example above shows:

* ``configure`` resolves the settings and configures logging before the body runs.
  Logging therefore uses the effective configuration from the first record.

* ``announce`` logs the resolved settings at debug level and then a version banner at
  info level. The debug record sits behind the level guard that `Logging (logging.py)`_
  recommends.

* ``run_async`` adapts an ``async def`` body to the synchronous callback that *Click*
  expects, and drives the body to completion with ``asyncio.run()``.

Decorators wrap from the bottom up but execute from the top down. Logging is therefore
configured first, the startup announcement follows, and the asynchronous body runs last.
The body enters ``app_lifespan()`` to acquire the shared resources for the lifetime of
the command.

Testing
-------

Tests run under *Pytest*. ``make test`` runs the unit tests, and ``make autotest`` runs
the system tests::

    make test
    make autotest

``make autotest`` reserves ``PYTEST_DEPLOYMENT`` for the URL of a deployed service that
system tests target. The default is ``http://localhost:8000``. The target prints the
value, and the shipped system tests do not read it.

The shared ``tests/conftest.py`` registers two markers, ``slow`` and ``requires_db``.
Test code applies them as ``@pytest.mark.slow`` and ``@pytest.mark.requires_db``. Each
marker has an option that skips the tests that carry it:

* ``slow`` marks tests that are expensive to run. Pass ``--skip-slow`` to skip them. The
  option has no effect until a test carries this marker.

* ``requires_db`` marks tests that need a live database. Pass ``--skip-db`` to skip
  them. Only the tests in ``tests/system`` carry this marker. As a result, ``--skip-db``
  affects only ``make autotest``.

The two options are independent and can be combined, for example
``PYTEST_EXTRA_OPTS="--skip-slow --skip-db"``.

The following Makefile variables customize a test run:

* ``PYTEST_EXTRA_OPTS`` forwards extra arguments to *Pytest*, such as the skip options
  above or any other *Pytest* flag.

* ``PYTEST_CUSTOM_PATH`` selects a path under the target's test directory, down to an
  individual module, class, or test. The test directory is ``tests/main`` for
  ``make test`` and ``tests/system`` for ``make autotest``.

* ``PYTEST_DURATIONS`` sets how many of the slowest tests the run reports, through the
  *Pytest* option ``--durations``. The default is ``10``.

* ``PYTEST_LOG_CLI`` enables *Pytest*'s live logging, which streams each log record to
  the console as the run proceeds. The default is ``false``. ``PYTEST_LOG_CLI_LEVEL``
  sets the threshold of live logging, by default ``INFO``. Live records render through
  *Pytest*'s own formatter as a raw dict, not in the application's JSON or console
  format. A traceback appears only for ``log.exception()`` records.

* ``PYTEST_CAPTURE`` selects *Pytest*'s output capture mode, through the option
  ``--capture``. The default is ``fd``, or ``no`` when ``PYTEST_LOG_CLI=true``.

For example::

    # Run only the tests under tests/main/<subdir>.
    make test PYTEST_CUSTOM_PATH=<subdir>

    # Run a single test by path.
    make test PYTEST_CUSTOM_PATH=<path/to/module.py>::<TestClass>::<test_method>

    # Skip slow tests.
    make test PYTEST_EXTRA_OPTS=--skip-slow

    # Skip tests that need a live database.
    make autotest PYTEST_EXTRA_OPTS=--skip-db

    # Repeat a single test 10 times to surface flakiness, through the --count
    # option of the pytest-repeat plugin. Pair it with PYTEST_CUSTOM_PATH, and
    # pick a test that exercises cached or global state, such as the settings
    # singleton here.
    make test \
      PYTEST_CUSTOM_PATH=app/core/test_config.py::TestGetSettings::test_reload_picks_up_changed_environment \
      PYTEST_EXTRA_OPTS=--count=10

Test utilities (``tests/utils.py``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The suite shares the following helpers, importable as
``from tests.utils import <func>``:

* ``fail_without_traceback(reason)`` fails the current test and reports only ``reason``,
  with no traceback. Use it for unmet external prerequisites, where a traceback adds no
  information.

* ``parse_json_lines(stream)`` parses a captured JSON-log ``StringIO`` into a list of
  records, one ``dict`` per line, and skips blank lines.

* ``assert_log_event(stream, match, *, count=1, **fields)`` asserts that exactly
  ``count`` captured records contain ``match`` as a substring of their ``event``. Every
  match must also contain each ``**fields`` pair, for example ``level="error"``. The
  helper returns the matches for further inspection.

* ``assert_log_exception(stream, match, exc_type, *, exc_value=None, level="error")``
  asserts that a single matching record logged an exception of ``exc_type``. It searches
  the whole structured ``exception`` chain and optionally checks ``exc_value``. Prefer
  it to indexing ``record["exception"]`` by hand, because it does not depend on the
  position of the exception in the chain.

* ``_database_url(...)`` builds a database URL from individual components. Each
  component defaults to a module-level constant: ``_DRIVER``, ``_USER``, ``_PASSWORD``,
  ``_HOST``, ``_PORT``, or ``_DATABASE``. ``VALID_DATABASE_URL`` is the URL with all
  defaults. These values back the ``database_*`` fixtures below.

Fixtures
^^^^^^^^

Fixtures are defined in ``conftest.py`` files and apply to every test at or below their
directory. ``pytest.ini`` runs *pytest-asyncio* in auto mode. As a result, async tests
need no ``@pytest.mark.asyncio`` marker, and async fixtures use the plain
``@pytest.fixture`` decorator.

``tests/conftest.py`` serves the whole suite:

* ``rng`` - a session-scoped, seeded ``random.Random``. The test header shows the seed,
  and ``{{ cookiecutter.env_prefix }}TEST_SEED`` pins it. This file also registers the
  ``slow`` and ``requires_db`` markers above.

``tests/main/conftest.py`` serves the unit tests that ``make test`` runs:

* ``reset_logging_state`` - automatic. It snapshots and restores the process-wide
  logging state around every test, which keeps one test's logging configuration from
  leaking into the next.

* ``_isolate_settings`` - automatic. Around every test, it removes the environment
  variable of each ``Settings`` field and ``{{ cookiecutter.env_prefix }}ENV_FILE``, and
  it clears the cached settings. It derives the variable names from the fields of
  ``Settings``, which lets a new setting work without a fixture change. ``.env.local``
  stays readable.

* ``valid_environment`` - supplies a valid database URL and replaces ``.env.local`` with
  an empty environment file. Request it in a test that needs valid settings independent
  of the developer's ``.env.local``.

* ``cap_json_logs`` - configures JSON logging to a ``StringIO`` and yields it. Read it
  with the helpers of ``tests/utils.py`` above.

* ``make_fake_stream`` - a factory for a fake stream with a configurable ``isatty()``,
  which exercises the color and TTY decisions.

* ``database_driver``, ``database_user``, ``database_password``, ``database_host``,
  ``database_port``, and ``database_name`` - the individual URL components.
  ``make_database_url`` is the URL factory, and ``valid_database_url`` is the URL with
  all defaults. Assert against these fixtures instead of hard-coded URL strings.

``tests/main/app/db/conftest.py`` serves the database unit tests:

* ``make_fake_sessionmaker`` - returns the ``FakeSessionMaker`` class. Pass an instance
  to ``create_session()`` in place of a real session factory. Its ``session`` attribute
  holds a ``FakeSession`` whose ``transaction`` is a ``FakeTransaction``. Inspect them
  to assert commit or rollback without a live database.

``tests/system/conftest.py`` serves the system tests that ``make autotest`` runs:

* ``app_logging`` - session-scoped and automatic. It configures logging as the
  application does, which keeps local variables out of logged tracebacks.

* ``database_url`` - session-scoped. It resolves the real database URL from
  ``{{ cookiecutter.env_prefix }}DATABASE_URL`` and fails the suite when the URL is
  unset or invalid, or the database is unreachable. Pass ``--skip-db`` to skip the suite
  instead. The URL is a ``SecretStr``, which keeps the password masked in the function
  arguments that *Pytest* prints in tracebacks. Call ``get_secret_value()`` only where a
  plain string is required. The masking does not extend to the frames of *SQLAlchemy*
  and the database driver. Do not pass ``--tb=long``, ``--full-trace``, or
  ``--showlocals`` where logs are shared.

* ``database_schema`` - session-scoped. It creates a dedicated ``itest_<random>`` schema
  for the run and drops it with ``CASCADE`` afterward.

* ``database_engine`` and ``database_sessionmaker`` - a real engine bound to the
  configured database, disposed after each test, and a session factory bound to that
  engine.

* ``items_table`` - creates an isolated table in the run schema and drops it after the
  test.

AI-Assisted Development
=======================

The generated project is prepared for the coding agents *Claude Code* and *OpenAI
Codex*. Both agents load its project instructions at the start of every session. They
load one of its agent skills when a task calls for it or when the user invokes the skill
by name.

Each asset has one canonical copy, stored where *Codex* reads it. A post-generation hook
symlinks it into the location that *Claude Code* reads. Edit only the canonical copy:

====================  ===========================  =========================
Asset                 Canonical copy (*Codex*)     Symlink (*Claude Code*)
====================  ===========================  =========================
Project instructions  ``AGENTS.md``                ``CLAUDE.md``
General instructions  ``AGENTS.override.md``       ``CLAUDE.local.md``
Reference files       ``.agents/docs/<topic>.md``  none; read on demand
Agent skills          ``.agents/skills/<name>/``   ``.claude/skills/<name>``
====================  ===========================  =========================

The symlinks are relative and belong under version control with the rest of the project.

Project Instructions
--------------------

``AGENTS.md`` in the project root gives an agent the knowledge that it cannot infer from
the code: the mandatory rules, the commands of the development workflow, the project
layout, and an index of reference files. *Codex* reads ``AGENTS.md`` natively, as
`Custom instructions with AGENTS.md`_ describes. *Claude Code* reads the symlink
``CLAUDE.md``, as `How Claude remembers your project`_ describes. From v2.1.277, *Claude
Code* also reads ``AGENTS.md`` directly, but by default only when no ``CLAUDE.md`` or
``CLAUDE.local.md`` exists in the working directory or above it. The generated project
contains ``CLAUDE.local.md``, and *Claude Code* therefore depends on the symlink.

``AGENTS.override.md`` in the project root holds general instructions that do not depend
on the project: output formatting, technical writing, documentation lookups for external
libraries, the use of *uv*, and code comments. *Claude Code* reads it through the
symlink ``CLAUDE.local.md`` and places it after ``CLAUDE.md``. *Codex* reads at most one
instruction file per directory and prefers ``AGENTS.override.md`` to ``AGENTS.md``. The
first instruction in ``AGENTS.override.md`` therefore directs *Codex* to read
``AGENTS.md``. *Codex* receives the project instructions through that file read, not
through automatic loading.

.. _`Custom instructions with AGENTS.md`: https://learn.chatgpt.com/docs/agent-configuration/agents-md
.. _`How Claude remembers your project`: https://code.claude.com/docs/en/memory

Cookiecutter renders the instruction files. They therefore name the package, the console
script, and the environment prefix of the generated project.

**Organization**

The instructions keep the context that every session pays for small:

* ``AGENTS.md`` is loaded into every session and holds only what applies to most tasks.

* ``AGENTS.override.md`` is loaded into every session as well and holds only rules that
  apply to any project.

* The reference files under ``.agents/docs`` are not loaded automatically. The
  *Reference* table in ``AGENTS.md`` names the tasks that each file serves, and the
  agent reads a file when its task enters that area:

  - ``architecture.md`` - components, startup flow, design decisions, configuration,
    logging, and recipes for adding a command, a setting, or a shared resource;
  - ``database.md`` - session and engine lifecycle, and the rationale behind the
    defaults;
  - ``conventions.md`` - code conventions that the analysis tools do not enforce on
    their own;
  - ``testing.md`` - test layout, running tests, fixtures, and helpers;
  - ``workflows.md`` - environment setup, quality checks, dependency management, builds,
    and execution plans;
  - ``infrastructure.md`` - the Docker image, the Compose stack, and their targets.

* Sections titled *Rules* are mandatory for the agent. All other content is context that
  informs its decisions. Where that context disagrees with the code, the code wins, and
  the instructions are corrected.

**Verification**

Start the agent in the root of the generated project and confirm that it loaded the
instructions:

* In *Claude Code*, run ``/context all``. ``CLAUDE.md`` and ``CLAUDE.local.md`` appear
  in the list under *Memory files*. ``/memory`` does not confirm loading, because it
  also lists the locations of files that do not exist.

* In *Codex*, run ``codex "Summarize the current instructions."``. The summary cites the
  rules from both ``AGENTS.override.md`` and ``AGENTS.md``. A summary that cites only
  ``AGENTS.override.md`` means that *Codex* did not follow the instruction to read
  ``AGENTS.md``.

*Codex* loads instruction files from the project root down to the working directory, and
it typically takes the Git root as the project root. Initialize the Git work tree first
to make the generated project that root, as `A Typical Session`_ shows.

**Maintenance**

* Edit ``AGENTS.md`` and ``AGENTS.override.md``, never ``CLAUDE.md`` or
  ``CLAUDE.local.md``. *Claude Code* refuses to write through the symlinks.

* Keep the instruction at the top of ``AGENTS.override.md`` that directs the agent to
  read ``AGENTS.md``. Without it, *Codex* does not see the project instructions.

* Update the instructions in the same change that alters a command, a path, a rule, or a
  design decision they describe. Delete an instruction that the code no longer supports.

* Keep ``AGENTS.md`` under 200 lines, because *Claude Code* recommends that size for
  reliable adherence. The limit also keeps the file well within the 32 KiB that *Codex*
  reads from project instruction files by default. Move detail that serves one area into
  a reference file, and list that file in the *Reference* table.

* The template occupies ``CLAUDE.local.md`` and ``AGENTS.override.md``. The agents
  otherwise leave these file names to the user for personal or temporary project
  instructions. Keep such instructions in the user-level files instead:
  ``~/.claude/CLAUDE.md`` for *Claude Code* and ``~/.codex/AGENTS.md`` for *Codex*.

* In the template, the instruction files are Jinja templates. Cookiecutter copies the
  skills without rendering them. Use the ``cookiecutter.*`` variables in the instruction
  files for project-specific names, and keep literal Jinja delimiters out of their text.

Skills
------

The bundled skills use the open `Agent Skills`_ format and run unchanged in
`Claude Code`_ and `OpenAI Codex`_. *Codex* reads the canonical copy of each skill in
``.agents/skills/<name>``. The post-generation hook symlinks it into ``.claude/skills``,
which *Claude Code* reads.

.. _`Agent Skills`: https://agentskills.io/
.. _`Claude Code`: https://code.claude.com/docs/en/skills
.. _`OpenAI Codex`: https://learn.chatgpt.com/docs/build-skills

.. contents:: Bundled Skills
   :local:
   :depth: 1
   :backlinks: none

Creating and Updating Tests (``update-tests``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Overview**

The ``update-tests`` skill creates new tests and improves existing ones at any test
level. It assumes no language, framework, or layout, and learns the tooling,
conventions, and test infrastructure from the project. Do not use it to debug a
production defect behind a single failing test.

**Usage**

Start the agent in the project root and invoke the skill with a mode, a path, and
optional instructions::

    <create|update> <path> [instructions]

In *Claude Code*, type ``/update-tests`` followed by the arguments. In *Codex*, mention
``$update-tests`` in the message. Both agents also select the skill on their own when a
request asks to write, review, refactor, or stabilize tests. The request then supplies
the arguments.

For example::

    # Create unit tests in a new directory for code that has none.
    /update-tests create tests/main/app/cli cover lazy subcommand loading

    # Create a single new test module.
    /update-tests create tests/main/app/test_runtime.py cover app_lifespan

    # Audit and refactor every test under a directory.
    /update-tests update tests/main/app/core

    # In Codex, direct the update toward a specific problem in one file.
    $update-tests update tests/main/test_logging.py focus on order dependence

The skill restates the resolved arguments, presents a plan before editing, and ends with
a report of its changes and how it verified them. It asks before it starts a service
that the tests need, such as PostgreSQL for the system tests, and starts the service
only through the project's own means. It stops the services it started before it
finishes, and it leaves services that were already running untouched.

**Arguments**

* ``mode`` (required) - ``create`` or ``update``:

  - ``create`` writes new tests at ``path`` for the code or behavior that the
    instructions name;
  - ``update`` audits the tests at ``path`` and refactors them to close coverage gaps,
    remove redundancy, strengthen weak assertions, and eliminate flakiness.

  When the first word is not a mode, the skill infers the mode from the request. It asks
  when the request supports both readings.

* ``path`` (required) - one directory or test file, relative to the working directory.
  It is the only location where the skill creates or changes tests. Changes to anything
  else, such as production code, shared fixtures, or dependencies, are proposed and
  applied only after approval. In ``update`` mode, the path must contain tests. In
  ``create`` mode, it may name a directory or file that does not exist yet, provided
  that its parent directory exists. Without a path, the skill asks for one instead of
  searching the project.

* ``instructions`` (optional) - free text after the path. In ``create`` mode, it names
  the code or behavior to test. Without instructions, the skill extends the existing
  tests at ``path``, and it asks what to test when there are none. In ``update`` mode,
  the instructions narrow or direct the work, for example toward a specific problem.
  They can also extend the work to code that no test at ``path`` exercises. Without such
  instructions, the skill lists that code as a follow-up, with the ``create`` invocation
  that would cover it.

Planning and Implementing Changes (``develop``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Overview**

The ``develop`` skill carries a substantial change from requirements to working,
documented code in three stages: planning, implementation, and optional testing. Each
stage starts only on the user's explicit approval. The skill suits new projects, new
features, ports from another codebase, language, or platform, imports of external
functionality, reimplementations, and integrations between existing systems. Like
``update-tests``, it assumes no language, framework, or layout and learns them from the
project. Do not use it to fix a single defect, make a small edit, refactor without
changing behavior, or work only on tests.

**Usage**

Start the agent in the project root and invoke the skill with an optional plan path and
a task::

    [plan-path] <task>

In *Claude Code*, type ``/develop`` followed by the arguments. In *Codex*, mention
``$develop`` in the message. The skill runs only when invoked by name. The agents do not
select it on their own, and an ordinary request does not start the staged process.

For example::

    # Plan a new feature; the plan goes to docs/exec-plans/active/.
    /develop add a migrate command that applies database schema migrations

    # Port behavior from another codebase.
    /develop port the retry policy of ../legacy-worker into the runtime

    # Keep the plan at a chosen path, then resume it in a later session.
    /develop docs/exec-plans/active/2026-11-12-health.md add a health command
    /develop docs/exec-plans/active/2026-11-12-health.md

    # In Codex, integrate an external system.
    $develop integrate the Redis cache from the Compose stack into the runtime

The skill restates the task, the plan location, and the starting stage before doing any
work, and ends each stage with a report.

**Stages and approval**

1. *Planning.* The skill studies the project, pins down the requirements, and designs
   the change. It uses a planning skill and the agent's plan mode when they are
   available. The default planning skill is `brainstorm`_. The stage ends with an
   execution plan, and nothing in the project changes before the plan is approved.

2. *Implementation.* After approval, the skill saves the plan, records a baseline of the
   checks and tests, and implements the plan milestone by milestone, keeping the plan
   current. A significant deviation, such as a changed requirement, interface, or
   dependency, waits for approval. Existing tests that an approved behavior change
   invalidates are updated in this stage, without weakening the coverage of unchanged
   behavior. New tests are not written. The stage ends with a report and the question
   whether to proceed with testing.

3. *Testing (optional).* The skill creates or updates the tests through ``update-tests``
   only when the user agrees, with one full invocation per approved target. The user may
   approve all proposed targets or a subset. The targets declined or left out are
   recorded as follow-ups in the plan and the tech-debt tracker.

Approval is never implied. Silence, a question, or a saved plan status does not count. A
plan resumed in a new session is presented for approval again, as is a plan changed in
substance since its approval. The skill stops after planning in a non-interactive run.
It then saves the draft plan where writes are permitted, and otherwise returns the plan
in its final message.

**Arguments**

* ``plan-path`` (optional) - the execution plan, relative to the working directory. An
  existing plan is resumed. A path that does not exist yet names the new plan file. The
  skill asks before using a path whose parent directory is missing, and it points out a
  location outside ``docs/exec-plans/`` before approval. Without a plan path, the plan
  goes to ``docs/exec-plans/active/``.

* ``task`` - free text that states the goal or points to the requirements, such as a
  specification, an issue, or the code to port. It may be omitted when the plan path
  resumes a plan.

**Execution plans**

Plans follow OpenAI's ExecPlans_ methodology. Each plan is a living, self-contained
document from which a later session can finish the work. It holds a progress log, a
record of discoveries, a decision log, and a retrospective. The skill keeps the plans in
the layout that `Harness engineering`_ describes::

    docs/exec-plans/
        active/                 plans in progress
        completed/              completed and cancelled plans
        tech-debt-tracker.md    deferred work and known shortcuts

A plan's file name is its creation date in ISO 8601 form followed by a short kebab-case
description, such as ``2026-11-12-health-command.md``. Every date and time in the plans
and the tracker is in UTC. A small change without design decisions gets a lightweight
plan. That plan needs approval like any other, but the skill saves it only when a plan
path is given. Project guidance in a file such as ``AGENTS.md`` may prescribe another
location than ``docs/exec-plans/``.

**Development standards**

The skill holds the implementation to built-in standards for completeness, correctness
and reliability, security, simplicity, maintainability, testability, and documentation.
It checks them itself before it reports the implementation as complete. The standards
turn review criteria into development rules: requirements traced to code and wired end
to end, errors and resources handled on every path, input validated and secrets kept out
of code and logs, the direct solution preferred over speculative abstraction, and user
documentation, agent instructions, and the plan updated in the same change. Test quality
remains the responsibility of ``update-tests``.

.. _`brainstorm`: https://github.com/umputun/cc-thingz#brainstorm
.. _`ExecPlans`: https://developers.openai.com/cookbook/articles/codex_exec_plans
.. _`Harness engineering`: https://openai.com/index/harness-engineering/
