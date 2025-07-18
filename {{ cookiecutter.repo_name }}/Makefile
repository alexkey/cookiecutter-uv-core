SHELL = /bin/bash

\t := $(NULL)	$(NULL)
define \n


endef


#---
# Definitions
#---

MACHINE = $(shell uname -m)
OS = $(shell uname -s)

CURDIR := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))
srcdir = $(CURDIR)/src
testdir = $(CURDIR)/tests
builddir = $(CURDIR)/build
distdir = $(CURDIR)/dist

PACKAGE_NAME = {{ cookiecutter.repo_name }}
PACKAGE_VERSION ?= $(strip \
	$(shell \
		grep "^ *version *= *" "${CURDIR}/pyproject.toml" \
		| tr -d '"' \
		| cut -d " " -f3 \
	) \
)

##
# Errors

ERROR_ENVIRONMENT = 1

which_helper = $(shell \
	[[ -n "$(shell which ${1} 2>/dev/null)" ]] \
		|| echo "echo ERROR: Can\'t find the command: ${1} && \
		exit ${ERROR_ENVIRONMENT}" \
)

##
# Commands

ifeq (${OS},Darwin)
	SED = gsed
ifeq ($(shell which ${SED}),)
	_install_hints += \
		Install GNU sed for macOS compatibility: `brew install gnu-sed`
endif
else
	SED = sed
endif

ifeq ($(shell which rg),)
	GREP = grep
else
	GREP = rg
endif

GIT = git

version_helper = $(shell ${1} --version | grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+")

##
# Python

PYTHON_VERSION_FILE ?= $(CURDIR)/.python-version

UV = uv
UV_VERSION = {{ cookiecutter.uv_version }}

UV_CACHE_DIR ?=
ifeq ($(shell which ${UV}),)
	_install_hints_python += \
		Install uv: https://docs.astral.sh/uv/getting-started/installation/
	UV_CACHE_DIR = "$(HOME)/.cache/uv"
endif

VIRTUALENV = $(if \
	${UV_PROJECT_ENVIRONMENT},${UV_PROJECT_ENVIRONMENT},${CURDIR}/.venv)
UV_LOCKFILE = $(CURDIR)/uv.lock

# A set of common options for the most frequently used `uv` commands.
UV_CMD_OPTS = \
	--directory="$(CURDIR)" \
	--python-preference=only-managed

UV_LOCK_EXTRA_OPTS ?=
UV_SYNC_EXTRA_OPTS ?=

INSTALL_EXTRAS ?=
ifdef INSTALL_EXTRAS
	UV_SYNC_OPT_DEPS = $(foreach extra,${INSTALL_EXTRAS}, --extra=${extra})
endif

##
# Docker

DOCKER = docker
DOCKER_BUILD_PLATFORM ?= {{ cookiecutter.docker_build_platform }}

DOCKER_PS_OPTS = \
	--all \
	--size
DOCKER_RM_OPTS = \
	--force \
	--volumes
DOCKER_SYSTEM_PRUNE_OPTS = \
	--all \
	--volumes
DOCKER_EXTRA_OPTS ?=

DOCKER_FILE ?= $(CURDIR)/docker/Dockerfile.$(MACHINE)
DOCKER_COMPOSE_FILE ?= $(CURDIR)/docker/docker-compose.yml
DOCKER_SERVICE_NAME ?= {{ cookiecutter.service_name }}
DOCKER_IMAGE_NAME ?= $(DOCKER_SERVICE_NAME):$(PACKAGE_VERSION)
DOCKER_MOUNT_POINT = /usr/local/src/$(PACKAGE_NAME)
DOCKER_SERVICE_PORT ?= 8000
DOCKER_CONTAINER_PORT ?= 8000
DOCKER_COMMAND ?= $(SHELL)

DOCKER_COMPOSE = $(DOCKER) compose $(DOCKER_EXTRA_OPTS)
define DOCKER_COMPOSE_EXPORTS
export CURDIR="$(CURDIR)" ; \
export DOCKER_IMAGE_NAME="$(DOCKER_IMAGE_NAME)" ; \
export DOCKER_BUILD_PLATFORM="$(DOCKER_BUILD_PLATFORM)" ; \
export DOCKER_MOUNT_POINT="$(DOCKER_MOUNT_POINT)" ; \
export DOCKER_SERVICE_PORT="$(DOCKER_SERVICE_PORT)" ; \
export DOCKER_CONTAINER_PORT="$(DOCKER_CONTAINER_PORT)"
endef

##
# Code quality

GIT_DEPTH ?= 1
PACKAGE_NOTES = \
	DEBUG \
	FIXME \
	TODO \
	XXX
NOTES_CONTEXT ?= 5
NOTES_EXCLUDE =
# Example usage:
#     NOTES_EXCLUDE = \
#	      $(notdir /path/to/dir) \
#	      Makefile \
#	      pylintrc
NOTES_EXCLUDE_FILTER = \
	$(foreach pattern,${NOTES_EXCLUDE}, /${pattern}/d;)

DEPTRY = deptry
RUFF = ruff
MYPY = mypy
MYPY_OPTS = \
	--install-types
PYLINT = pylint
PYLINT_OPTS = \
	--output-format=colorized
PYTEST = pytest
PYTEST_UNIT_DIR = main
PYTEST_SYSTEM_DIR = system
PYTEST_DURATIONS ?= 10
PYTEST_LOG_CLI ?= false
PYTEST_LOG_CLI_LEVEL ?= INFO
PYTEST_OPTS = \
	-vv \
	--capture=no \
	--durations=$(PYTEST_DURATIONS) \
	--override-ini="log_cli=$(PYTEST_LOG_CLI)" \
	--override-ini="log_cli_level=$(PYTEST_LOG_CLI_LEVEL)"
# 	--asyncio-mode=auto  # <- Manages Pytest asynchronous test execution:
#                        #    * Creates new event loop per test
#                        #    * Handles mixed synchronous/asynchronous tests
#                        #    * Ensures proper loop cleanup
PYTEST_EXTRA_OPTS ?=
PYTEST_CUSTOM_PATH ?=
define PYTEST_EXPORTS
# Optionally add exports to be passed to Pytest HERE.
endef


#---
# Targets
#---

all:
	@echo "$(PACKAGE_NAME) $(PACKAGE_VERSION) ($(OS) @ $(MACHINE) [$(VIRTUALENV)])"
	@echo "Type \`make help\` for a list of available targets"

.PHONY: env-check
# target: env-check - Check the local environment for requirements
env-check:
ifdef _install_hints
	$(info ${_install_hints})
endif
	@$(call which_helper,${SED})
	@$(call which_helper,${GREP})
	@$(call which_helper,${GIT})

.PHONY: env-check-python
# target: env-check-python - Check the requirements for Python
env-check-python:
ifeq ($(wildcard ${PYTHON_VERSION_FILE}),)
	$(error The Python version must be set explicitly in the file \
		`${PYTHON_VERSION_FILE}`)
endif
ifdef _install_hints_python
	$(info ${_install_hints_python})
endif
	@$(call which_helper,${UV})

	@uv_ver="$(call version_helper,${UV})" ; \
	if [[ "$${uv_ver}" != "$(UV_VERSION)" ]]; then \
		echo "WARNING: Incompatible \`${UV}\` version: $${uv_ver} (expected " \
			"${UV_VERSION})" ; \
	fi

.PHONY: env-check-venv
# target: env-check-venv - Ensure the virtual environment exists
env-check-venv:
ifeq ($(wildcard ${VIRTUALENV}),)
	$(error The virtual environment is missing at the target path: \
		`${VIRTUALENV}`)
endif

.PHONY: env-check-lockfile
# target: env-check-lockfile - Ensure the lockfile exists
env-check-lockfile:
ifeq ($(wildcard ${UV_LOCKFILE}),)
	$(error The project lockfile does not exist: `${UV_LOCKFILE}`)
endif
	$(info Requires that the project lockfile (`uv.lock`) is up-to-date. \
		If the lockfile is needs to be updated, the target will exit with an \
		error \
	)

.PHONY: env-show-python
# target: env-show-python - Display the environment variables used to configure Python and related tools
env-show-python:
	$(info UV_VERSION -> `$(UV_VERSION)`)
	$(info UV_CACHE_DIR -> `$(UV_CACHE_DIR)`)
	$(info VIRTUALENV -> `$(VIRTUALENV)`)
	$(info UV_LOCKFILE -> `$(UV_LOCKFILE)`)
	$(info UV_CMD_OPTS -> `$(UV_CMD_OPTS)`)

ifdef UV_LOCK_EXTRA_OPTS
	$(info UV_LOCK_EXTRA_OPTS -> `$(UV_LOCK_EXTRA_OPTS)`)
else
	$(info UV_LOCK_EXTRA_OPTS:)
	$(info ${\t}Use "--upgrade" to allow package upgrades, ignoring pinned \
		versions)
	$(info ${\t}Use "--upgrade-package=<name>" to allow upgrades for the \
		specified package)
endif

ifdef UV_SYNC_EXTRA_OPTS
	$(info UV_SYNC_EXTRA_OPTS -> `$(UV_SYNC_EXTRA_OPTS)`)
else
	$(info UV_SYNC_EXTRA_OPTS:)
	$(info ${\t}Use "--all-extras" to include all optional dependencies)
	$(info ${\t}Use "--inexact" to keep extraneous packages present in the \
		environment)
	$(info ${\t}Use "--reinstall" to refresh all cached data and reinstall \
		all packages)
endif

ifdef INSTALL_EXTRAS
	$(info INSTALL_EXTRAS -> `$(INSTALL_EXTRAS)`)
endif

.PHONY: env-check-docker
# target: env-check-docker - Check the requirements for Docker
env-check-docker:
	@$(call which_helper,${DOCKER})

.PHONY: env-check-qa
# target: env-check-qa - Check the requirements for the quality assurance tools
env-check-qa: env-check-python
	@$(call which_helper,${DEPTRY})
	@$(call which_helper,${RUFF})
	@$(call which_helper,${MYPY})
	@$(call which_helper,${PYLINT})
	@$(call which_helper,${PYTEST})

.PHONY: env-show-qa
# target: env-show-qa - Display the environment variables used to configure the quality assurance tools
env-show-qa:
	$(info MYPY_OPTS -> `$(MYPY_OPTS)`)
	$(info PYLINT_OPTS -> `$(PYLINT_OPTS)`)

	$(info PYTEST_UNIT_DIR -> `$(PYTEST_UNIT_DIR)`)
	$(info PYTEST_SYSTEM_DIR -> `$(PYTEST_SYSTEM_DIR)`)

ifdef PYTEST_DURATIONS
	$(info PYTEST_DURATIONS -> `$(PYTEST_DURATIONS)`)
endif
ifdef PYTEST_LOG_CLI
	$(info PYTEST_LOG_CLI -> `$(PYTEST_LOG_CLI)`)
endif
ifdef PYTEST_LOG_CLI_LEVEL
	$(info PYTEST_LOG_CLI_LEVEL -> `$(PYTEST_LOG_CLI_LEVEL)`)
endif

	$(info PYTEST_OPTS -> `$(PYTEST_OPTS)`)
ifdef PYTEST_EXTRA_OPTS
	$(info PYTEST_EXTRA_OPTS -> `$(PYTEST_EXTRA_OPTS)`)
else
	$(info PYTEST_EXTRA_OPTS: Use "--skip-slow" to exclude slow tests)
endif

ifdef PYTEST_CUSTOM_PATH
	$(info PYTEST_CUSTOM_PATH -> `$(PYTEST_CUSTOM_PATH)`)
else
	$(info PYTEST_CUSTOM_PATH: Use "/path/to/test.py::TestClass::test_method" to run a \
		single test `test_method` from the suite `TestClass` of the `test.py`)
endif
ifdef PYTEST_EXPORTS
	$(info PYTEST_EXPORTS -> `$(PYTEST_EXPORTS)`)
endif

##
# Python

.PHONY: venv
# target: venv - Create a virtual environment
venv: env-check-python
ifneq ($(wildcard ${VIRTUALENV}),)
	$(error A virtual environment already exists at the target path: \
		`${VIRTUALENV}`)
endif
	@$(UV) venv $(UV_CMD_OPTS) --seed "$(VIRTUALENV)"

.PHONY: requirements
# target: requirements - Update the project's lockfile
requirements: env-check-python
# If the project lockfile (`uv.lock`) does not exist, it will be created.
# If a lockfile is present, its contents will be used as preferences for the
# resolution process.
	@$(UV) lock $(UV_CMD_OPTS) $(UV_LOCK_EXTRA_OPTS)

.PHONY: install
# target: install - Ensure that all project dependencies are up to date with the lockfile
install: env-check-python env-check-venv env-check-lockfile
	@$(UV) sync $(UV_CMD_OPTS) --locked \
		$(UV_SYNC_OPT_DEPS) $(UV_SYNC_EXTRA_OPTS)

##
# Auxiliary

.PHONY: help
# target: help - Display all callable targets
help: env-check
	@echo
	@$(GREP) "^\s*#\s*target\s*:\s*" [Mm]akefile \
		| $(SED) -r "s/^\s*#\s*target\s*:\s*//g"

.PHONY: clean
# target: clean - Clean the project's directory
clean: env-check
	@find "$(CURDIR)" \
		-name ".mypy_cache" -type d -exec rm -vrf {} + -o \
		-name ".pytest_cache" -type d -exec rm -vrf {} + -o \
		-name ".ruff_cache" -type d -exec rm -vrf {} + -o \
		-name "__pycache__" -type d -exec rm -vrf {} + -o \
		-name "*.py[cod]" -exec rm -vf {} +

.PHONY: distclean
# target: distclean - Clean the project's build output
distclean: env-check
	@find "$(CURDIR)" \
		-path "$(VIRTUALENV)" -prune -o \
		-name "*.dist-info" -type d -exec rm -vrf {} + -o \
		-name "*.egg-info" -type d -exec rm -vrf {} + -o \
		-name "*.so" -exec rm -vf {} +
	@rm -vrf \
		"$(builddir)" \
		"$(distdir)"

.PHONY: mostlyclean
# target: mostlyclean - Delete almost everything
mostlyclean: env-check clean distclean
	@find "$(CURDIR)" -name .DS_Store -exec rm -vf {} +
	@if [[ -n "$(UV_CACHE_DIR)" ]]; then \
		rm -vrf "$(UV_CACHE_DIR)"; \
	else \
		$(UV) cache clean; \
	fi
	@rm -vrf "$(VIRTUALENV)"
