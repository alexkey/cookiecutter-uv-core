====================
cookiecutter-uv-core
====================

;;

Get Started
-----------

;;

Prerequisites
-------------

To build, package, and work with this project, several tools must be installed.

Ensure the following tools are available on your system:

* GNU make;
* GNU sed: install with ``brew install gnu-sed`` on macOS;
* ripgrep: optional but recommended (``cargo install ripgrep``);
* Git;
* uv_ ({{ cookiecutter.uv_version }});
* Docker Desktop (on macOS), or Docker Engine with QEMU installed [#docker]_.

The following tools will be installed as project developer dependencies
(automatically during the creation of the virtual environment):

* Deptry_;
* Ruff_;
* Mypy_;
* Pylint_;
* Pytest_.

.. _uv: https://docs.astral.sh/uv/

.. [#docker] `Simple multi-platform build using emulation with Docker <https://docs.docker.com/build/building/multi-platform/#simple-multi-platform-build-using-emulation>`_.

**Environment**

Ensure that all required tools are installed and functioning correctly, and
inspect the active configuration of the project by running the provided
commands:

* Simply type ``make`` to view the project version and the current environment
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

  - Update the lockfile: ``make requirements``;
  - Refresh all cached data and update the lockfile:
    ``make requirements-refresh``;
  - Preview a package upgrade without writing the lockfile:
    ``make requirements-try``;
  - Upgrade packages, ignoring pinned versions, then install them:
    ``make requirements-up``;
  - List and validate the installed packages: ``make requirements-check``;
  - Display the dependency tree: ``make requirements-tree``.

* Synchronize the virtual environment with the lockfile: ``make install``.

* Reinstall all dependencies: ``make force-install``.

* Build the source and wheel distributions: ``make dist``.

**Managing Docker**

The project provides a set of targets to build images, run containers, and
manage Docker resources:

* Show all images, containers, and volumes: ``make docker-info``.

* Build an image from the Dockerfile: ``make docker-build``.

* Create and run a container from the image, removed on exit:
  ``make docker-run``.

* Manage the service stack with Compose:

  - Build, start, then tear down the containers: ``make docker-compose``;
  - Follow the logs from the running containers: ``make docker-logs``;
  - Open a shell in the running container: ``make docker-shell``.

  For example, surface errors, warnings, and other problems in the log
  stream with ripgrep::

      make docker-logs | rg -i "(err|crit|kill|garbage|warn)"

* Remove all images, containers, and volumes: ``make docker-clean``.

**Auxiliary Targets**

The project includes several utility targets to help manage it:

* View all available targets: ``make help``.

* Clean various cache files and bytecode: ``make clean``.

* Clean build and distribution outputs: ``make distclean``.

* Perform a complete cleanup (cache, virtual environment, and all):
  ``make mostlyclean``.
