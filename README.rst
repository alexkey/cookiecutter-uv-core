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
  (it should be checked within the virtual environment at a later stage).

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

  Set ``PYTEST_DEPLOYMENT`` to the deployed service URL that the system
  tests target, e.g., ``http://localhost:8000`` for the local environment.

**Auxiliary Targets**

The project includes several utility targets to help manage it:

* View all available targets: ``make help``.

* Clean various cache files and bytecode: ``make clean``.

* Clean build and distribution outputs: ``make distclean``.

* Perform a complete cleanup (cache, virtual environment, and all):
  ``make mostlyclean``.

Usage
-----

The generated service provides two foundational runtime facilities: typed
configuration and structured logging.

**Configuration**

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

**Logging**

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
