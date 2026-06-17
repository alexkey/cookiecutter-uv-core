====================
cookiecutter-uv-core
====================

*cookiecutter-uv-core* is a Cookiecutter_ template for scaffolding modern
Python services managed with uv_. It generates a typed ``src``-layout package
with essential foundations already in place, including layered configuration
with Pydantic, structured logging with *structlog*, asynchronous *SQLAlchemy*
access to PostgreSQL, a CLI entry point, and multi-platform Docker images.

The template also includes a comprehensive Makefile-driven workflow for
dependency management, containerization, code quality, and testing.

Get Started
-----------

This repository is a Cookiecutter_ template for generating a new Python service
with the project structure, tooling, and development workflow already set up.

Use ``uvx``, the tool runner included with *uv*, to run Cookiecutter in an
isolated environment without installing it separately.

From a local clone of this repository, run::

    uvx cookiecutter --output-dir </path/to/dir> --overwrite-if-exists .

Cookiecutter uses ``.`` as the template in the current directory and creates
the generated project inside ``--output-dir`` (``-o``).

To generate from a remote repository instead, pass a GitHub repository
reference using the ``gh:<owner>/<repo>`` form in place of ``.``::

    uvx cookiecutter -o </path/to/dir> gh:alexkey/cookiecutter-uv-core

Cookiecutter will prompt you for the following values. Press Enter to accept
the default shown for each prompt:

* ``name`` - the project's display name, for example ``FooBar-baz``. This value
  is used to derive ``service_name``, ``repo_name``, and ``env_prefix``.
* ``version`` - the initial project version.
* ``brief`` - a short one-line package summary.
* ``description`` - a longer description used in the generated README.
* ``author_name`` and ``author_email`` - the author and maintainer details.
* ``url`` and ``repository`` - the project homepage and source repository URLs.
* ``license`` - the `SPDX license identifier`_.
* ``uv_version`` and ``python_version`` - the pinned *uv* and CPython versions.
* ``docker_build_platform`` - the target platform for Docker image builds.
* ``redis_image_tag`` and ``postgres_image_tag`` - the Docker Compose service
  image tags.
* ``postgres_user`` - the PostgreSQL user.

The following values are derived automatically from the inputs above. You can
usually accept their defaults unless you have a specific reason to override
them:

* ``service_name`` - the lowercased project name.
* ``repo_name`` - the importable Python package name, with hyphens replaced by
  underscores.
* ``env_prefix`` - the prefix used for settings environment variables.
* ``python_majmin`` - the major and minor Python version.
* ``docker_compose_name`` - the Docker Compose project name.
* ``docker_prefix`` - the base path used inside Docker images.
* ``year`` - the current year.

To generate a sample project using only the built-in defaults, run Cookiecutter
with ``--no-input``::

    uvx cookiecutter -o </path/to/dir> --no-input .

This creates a sample ``foobar_baz`` project that you can inspect, test, or
discard.

For the full list of Cookiecutter options, run::

    uvx cookiecutter --help

After generating the project, change into its directory and follow the
`Prerequisites`_ and `Features`_ sections below to verify your tools, create
the environment, and start working.

.. _Cookiecutter: https://cookiecutter.readthedocs.io/
.. _uv: https://docs.astral.sh/uv/
.. _`SPDX license identifier`: https://spdx.org/licenses/

Prerequisites
-------------

To build, package, and work with this project, several tools must be installed.

Ensure the following tools are available on your system:

* GNU make;
* GNU sed: install with ``brew install gnu-sed`` on macOS;
* ripgrep: optional but recommended (``cargo install ripgrep``);
* Git;
* *uv* ({{ cookiecutter.uv_version }});
* Docker Desktop (on macOS), or Docker Engine with QEMU installed [#docker]_.

The following tools will be installed as project developer dependencies
(automatically during the creation of the virtual environment):

* Deptry_;
* Ruff_;
* Mypy_;
* Pylint_;
* Pytest_.

.. [#docker] `Simple multi-platform build using emulation with Docker <https://docs.docker.com/build/building/multi-platform/#simple-multi-platform-build-using-emulation>`_.

**Environment**

Ensure that all required tools are installed and functioning correctly, and
inspect the active configuration of the project by running the provided
commands:

* Type ``make`` to view the project version and the current environment
  details.

* Check the primary tools by running: ``make env-check``.

* Check Python-specific requirements:

  - General requirements: ``make env-check-python``;
  - Verify the project lockfile: ``make env-check-lockfile``;
  - Ensure the virtual environment exists: ``make env-check-venv``.

* Display the environment variables used to configure Python and related
  tools: ``make env-show-python``.

* Check Docker-specific requirements: ``make env-check-docker``.

* Display the environment variables used to configure Docker:
  ``make env-show-docker``.

* Check the requirements for quality assurance tools: ``make env-check-qa``
  (run this check from within the virtual environment at a later stage).

* Display the environment variables used to configure the quality assurance
  tools: ``make env-show-qa``.

.. _Deptry: https://deptry.com/
.. _Ruff: https://docs.astral.sh/ruff/
.. _Mypy: https://mypy-lang.org/
.. _Pylint: https://pylint.readthedocs.io/en/latest/
.. _Pytest: https://docs.pytest.org/en/stable/

Features
--------

**Managing Python**

The project provides a set of targets to manage the Python virtual environment,
dependencies, and package distributions:

* Create a virtual environment: ``make venv``.

* Manage the project's dependencies and lockfile:

  - Update the lockfile: ``make requirements`` (set
    ``UV_LOCK_EXTRA_OPTS`` to ``--upgrade-package=<name>`` to allow upgrades
    for the specified package);
  - Refresh all cached data and update the lockfile:
    ``make requirements-refresh``;
  - Preview a package upgrade without writing the lockfile:
    ``make requirements-try``;
  - Upgrade packages, ignoring pinned versions, then install them:
    ``make requirements-up``;
  - List and validate the installed packages: ``make requirements-check``;
  - Display the dependency tree: ``make requirements-tree``.

* Synchronize the virtual environment with the lockfile: ``make install``.
  Set ``UV_SYNC_EXTRA_OPTS`` to:

  - ``--all-extras`` to include all optional dependencies;
  - ``--inexact`` to keep extraneous packages present in the environment.

* Reinstall all dependencies: ``make force-install``.

* Build the source and wheel distributions: ``make dist``.

**Managing Docker**

The project provides a set of targets to build images, run containers, and
manage Docker resources:

* Show all images, containers, and volumes: ``make docker-info``.

* Build an image from the Dockerfile: ``make docker-build``. Set
  ``DOCKER_EXTRA_OPTS`` to ``--progress=plain`` to show the full build output.

* Create and run a container from the image, removed on exit:
  ``make docker-run``. Set ``DOCKER_EXTRA_OPTS`` to
  ``--publish 127.0.0.1:8000:8000`` to publish the container's port on the
  host.

* Manage the service stack with Compose:

  - Build, start, then tear down the containers: ``make docker-compose``;
  - Follow the logs from the running containers: ``make docker-logs``;
  - Open a shell in the running container: ``make docker-shell``.

  For example, surface errors, warnings, and other problems in the log
  stream with ripgrep::

      make docker-logs | rg -i "(err|crit|kill|garbage|warn)"

* Remove all images, containers, and volumes: ``make docker-clean``.

**Code Quality**

The project provides a set of targets to inspect notes, analyze dependencies,
lint, format, and test the codebase:

* List source code notes, showing ``NOTES_CONTEXT`` lines of surrounding
  context:

  - List all notes, sorted by tag: ``make show-notes``;
  - List notes from the most recent commits and modified files, scanning the
    last ``GIT_DEPTH`` commits: ``make show-notes-recent``.

* Find unused, missing, and transitive dependencies: ``make check-deps``.
  Tune Deptry's settings in the ``[tool.deptry]`` section of
  ``pyproject.toml``.

* Analyze the code:

  - Lint with Ruff: ``make check-ruff``;
  - Perform static type checking with Mypy: ``make check-mypy``;
  - Perform code analysis with Pylint: ``make check-pylint``;
  - Run all of the above analysis tools at once: ``make lint``.

  The quality assurance tools are configured by the ``MYPY_OPTS`` and
  ``PYLINT_OPTS`` variables and the ``mypy.ini``, ``pytest.ini``, and
  ``pylintrc`` files.

* Manage code formatting:

  - Detect unformatted files: ``make check-format``;
  - Sort imports and format all Python files: ``make format``.

* Run tests:

  - Run the unit tests in the ``PYTEST_UNIT_DIR`` subdirectory of
    ``tests``: ``make test``;
  - Run the system tests in the ``PYTEST_SYSTEM_DIR`` subdirectory of
    ``tests``: ``make autotest``.

  ``make autotest`` reads ``PYTEST_DEPLOYMENT`` as its target deployment URL,
  currently a stub.

  Both targets also accept ``PYTEST_EXTRA_OPTS`` and ``PYTEST_CUSTOM_PATH`` to
  forward extra Pytest arguments and restrict the run to specific paths; see
  *Testing* under the section `Usage`_ for details.

**Auxiliary Targets**

The project includes several utility targets to help manage it:

* View all available targets: ``make help``.

* Clean various cache files and bytecode: ``make clean``.

* Clean build and distribution outputs: ``make distclean``.

* Perform a complete cleanup (cache, virtual environment, and all):
  ``make mostlyclean``.

Usage
-----

The generated service provides three foundational runtime facilities: typed
configuration, structured logging, and asynchronous database access.

**Configuration** (``config.py``)

Runtime configuration is centralized in a typed Pydantic ``Settings`` model and
read through a cached accessor::

    from {{ cookiecutter.repo_name }} import get_settings

    settings = get_settings()

* Settings are populated from environment variables that share the project's
  prefix, for example ``{{ cookiecutter.env_prefix }}LOG_LEVEL`` and
  ``{{ cookiecutter.env_prefix }}DATABASE_URL``. Names are case-sensitive, and
  variables that do not map to a defined setting are rejected.

* Values may also be supplied through an env file, ``.env.local`` by default;
  set ``{{ cookiecutter.env_prefix }}ENV_FILE`` to load a different path.
  Process environment variables take precedence over the env file. See
  ``.env.local`` for the full set of supported variables.

* ``get_settings()`` returns a cached singleton. Pass ``reload=True`` to
  discard the cache and rebuild it from the current environment.

* ``DATABASE_URL`` is required and validated: it must use the
  ``postgresql+asyncpg`` driver and include a host and a database name. It is
  held as a ``SecretStr`` and masked when settings are logged or printed.

**Logging** (``logging.py``)

Logging is built on *structlog* and applies uniformly to records emitted
through both *structlog* and the standard library. Configure it once during
startup, driving it from the settings above::

    from {{ cookiecutter.repo_name }} import get_logger, get_settings, setup_logging

    settings = get_settings()

    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        enable_colors=settings.LOG_COLORS,
    )

    logger = get_logger(__name__)
    logger.info("service started")

* Call ``setup_logging()`` once before emitting logs. It may be called again to
  reconfigure logging at runtime.

* ``log_format`` selects the renderer: ``console`` for human-readable output
  and ``json`` for machine-readable structured logs. ``log_level`` sets the
  threshold below which records are dropped; level names are case-insensitive.

* Colors apply to ``console`` output only on a TTY and are suppressed when the
  ``NO_COLOR`` environment variable is set.

* Retrieve module-level loggers with ``get_logger(__name__)`` and bind context
  as keyword arguments. Guard expensive log preparation with
  ``is_level_enabled(logger)``.

**Database** (``database.py``)

Database access uses asynchronous *SQLAlchemy* over the ``postgresql+asyncpg``
driver. Helper functions cover the full lifecycle: creating and disposing the
engine, building a session factory, and opening sessions that commit or roll
back automatically::

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

* Create the engine once with ``create_engine()`` and reuse it for the process
  lifetime; it owns the connection pool. Creation failures return ``None`` by
  default; pass ``raise_on_exc=True`` to fail fast at startup. Dispose the
  engine once during shutdown with ``await dispose_engine(engine)`` to close
  pooled connections.

* Build a single session factory per engine with ``create_sessionmaker()`` and
  share it as the source of every session. Do not create an engine or factory
  per request or per task.

* ``create_session()`` is an async context manager that opens one session and
  wraps the enclosed block in a single transaction. The transaction commits
  when the block exits cleanly and rolls back on any exception; the session is
  always closed. Use one block per unit of work and let it own the boundary -
  do not call ``session.begin()`` or ``session.commit()`` yourself inside it.

  - Database and unexpected errors are re-raised after rollback by default
    (``raise_on_exc=True``); ``asyncio.CancelledError`` always rolls back and
    propagates. Pass ``context=...`` to label a session in log records and
    ``verbose=True`` to trace each lifecycle step.

* **The defaults** applied to the engine and sessions live in
  ``DEFAULT_ASYNC_ENGINE_PARAMS`` and ``DEFAULT_ASYNC_SESSION_PARAMS``; consult
  them for the active values and override any of them through keyword arguments
  to ``create_engine()`` and ``create_sessionmaker()``.

  - Sessions set ``expire_on_commit=False``. With the default ``True``,
    attributes are expired after ``commit()``, so the first later access to
    each attribute triggers an implicit refresh SELECT. Under asyncio, that
    implicit I/O can occur outside *SQLAlchemy*'s async bridge and raise
    ``MissingGreenlet``. The tradeoff is that post-commit objects are not
    automatically re-fetched. Server-generated values such as
    ``server_default``, ``server_onupdate``, and ``Computed`` are available
    only if *SQLAlchemy* populated them during flush, typically via
    ``RETURNING`` where supported; values that were not populated remain
    expired and trigger the same implicit I/O problem on access. Separately, if
    *SQLAlchemy* is not configured to know about a server-side computation, the
    affected value may remain stale in memory. Fetch such values explicitly
    with ``await session.refresh(obj, [...])``, and load relationships eagerly
    with ``selectinload()`` rather than relying on attribute access.

  - The engine pool settings are designed to work together when connections
    pass through intermediaries. ``pool_pre_ping`` verifies health when a
    connection is retrieved from the pool and automatically replaces it if it
    was dropped while idle. ``pool_use_lifo`` keeps traffic on a smaller set of
    active connections, allowing excess connections to remain idle and be
    closed by the server during low-traffic periods. ``pool_recycle`` (1800
    seconds) limits connection age and is a reasonable default when no
    component in the network path closes connections sooner. If you are using
    PgBouncer (600s default), a load balancer, or NAT (for example, an AWS NLB
    with a 350s idle timeout), set it below the shortest idle timeout in the
    path, typically around 300 seconds. While ``pool_pre_ping`` detects stale
    connections when they are retrieved from the pool, ``pool_recycle`` helps
    avoid reaching that state in the first place.

**Testing**

Tests run under *Pytest*. As mentioned above, the ``make test`` and
``make autotest`` targets run the project's tests::

    make test
    make autotest

``PYTEST_DEPLOYMENT`` is dedicated to ``make autotest`` and is reserved for the
deployed service URL that system tests will target (default
``http://localhost:8000``). It is currently a stub: ``make autotest`` only
echoes the value, and the shipped system tests do not consume it yet.

The shared ``{{ cookiecutter.repo_name }}/tests/conftest.py`` registers two
markers, applied in test code as ``@pytest.mark.slow`` and
``@pytest.mark.requires_db``, each paired with an option that skips the tests
carrying it:

* ``slow`` marks tests that are expensive to run; pass ``--skip-slow`` to skip
  them.

* ``requires_db`` marks tests that need a live database; pass ``--skip-db`` to
  skip them.

The two options are independent and may be combined, for example
``PYTEST_EXTRA_OPTS="--skip-slow --skip-db"``.

Two Makefile variables customize any test run:

* ``PYTEST_EXTRA_OPTS`` forwards extra arguments to Pytest, such as the skip
  options above or any other Pytest flag.

* ``PYTEST_CUSTOM_PATH`` specifies a path under the target's test directory
  (``tests/main`` for ``make test`` and ``tests/system`` for
  ``make autotest``), down to an individual module, class, or test.

For example::

    # Run only the tests under tests/main/<subdir>.
    make test PYTEST_CUSTOM_PATH=<subdir>

    # Run a single test by path.
    make test PYTEST_CUSTOM_PATH=<path/to/module.py>::<TestClass>::<test_method>

    # Skip slow tests.
    make test PYTEST_EXTRA_OPTS=--skip-slow

    # Skip tests that need a live database.
    make test PYTEST_EXTRA_OPTS=--skip-db
