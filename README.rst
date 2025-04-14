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

- GNU make;
- GNU sed: install with ``brew install gnu-sed`` on macOS;
- ripgrep: optional but recommended (``cargo install ripgrep``);
- Git;
- uv_ ({{ cookiecutter.uv_version }});
- Docker Desktop (on macOS), or Docker Engine with QEMU installed [#docker]_.

The following tools will be installed as project developer dependencies
(automatically during the creation of the virtual environment):

- Deptry_;
- Ruff_;
- Mypy_;
- Pylint_;
- Pytest_.

.. _uv: https://docs.astral.sh/uv/

.. [#docker] `Simple multi-platform build using emulation with Docker <https://docs.docker.com/build/building/multi-platform/#simple-multi-platform-build-using-emulation>`_.

**Environment Checkers**

Ensure that all required tools are installed and functioning correctly by
running the provided environment check commands:

- Simply type ``make`` to view the project version and the current environment
  details.

- Check the primary tools by running: ``make env-check``.

- Check Python-specific requirements:
  * General requirements: ``make env-check-python``;
  * Verify the project lockfile: ``make env-check-lockfile``;
  * Ensure the virtual environment exists: ``make env-check-venv``.

- Check Docker-specific requirements: ``make env-check-docker``.

- Check the requirements for quality assurance tools: ``make env-check-qa``
  (it should be checked within the virtual environment at a later stage).

.. _Deptry: https://deptry.com/
.. _Ruff: https://docs.astral.sh/ruff/
.. _Mypy: https://mypy-lang.org/
.. _Pylint: https://pylint.readthedocs.io/en/latest/
.. _Pytest: https://docs.pytest.org/en/stable/

Features
--------

**Auxiliary Targets**

The project includes several utility targets to help manage the project:

- View all available targets: ``make help``.

- Clean various cache files and bytecode: ``make clean``.

- Clean build and distribution outputs: ``make distclean``.

- Perform a complete cleanup (cache, virtual environment, and all):
  ``make mostlyclean``.
