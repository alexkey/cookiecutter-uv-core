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
UV_BUILD_OPTS = \
	--verify-hashes

UV_LOCK_EXTRA_OPTS ?=
UV_SYNC_EXTRA_OPTS ?=
UV_BUILD_EXTRA_OPTS ?=

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
DOCKER_CONTAINER_PORT ?= 8000
DOCKER_HOST_PORT ?= 8000
DOCKER_COMMAND ?= $(SHELL)

# List of variables to pass as build args.
DOCKER_ARGS = \
	PACKAGE_NAME \
	DOCKER_MOUNT_POINT \
	DOCKER_CONTAINER_PORT
DOCKER_BUILD_ARGS = $(foreach arg,${DOCKER_ARGS}, --build-arg "${arg}=${$(arg)}")

DOCKER_COMPOSE = $(DOCKER) compose $(DOCKER_EXTRA_OPTS)
define DOCKER_COMPOSE_EXPORTS
export CURDIR="$(CURDIR)" ; \
export DOCKER_IMAGE_NAME="$(DOCKER_IMAGE_NAME)" ; \
export DOCKER_BUILD_PLATFORM="$(DOCKER_BUILD_PLATFORM)" ; \
export DOCKER_MOUNT_POINT="$(DOCKER_MOUNT_POINT)" ; \
export DOCKER_CONTAINER_PORT="$(DOCKER_CONTAINER_PORT)" ; \
export DOCKER_HOST_PORT="$(DOCKER_HOST_PORT)"
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
PYTEST_DEPLOYMENT ?= http://localhost:8000
# Optionally add exports to be passed to Pytest HERE ==>
define PYTEST_EXPORTS
:
endef

define show_notes_helper
	@for tag in $(PACKAGE_NOTES); do \
		echo -e "\n#---\n# $${tag}\n#---\n" ; \
		$(GREP) --context=$(NOTES_CONTEXT) "[^=]\b$${tag}\b" $$( \
			${1} \
			| sort -u \
			| ${SED} '${NOTES_EXCLUDE_FILTER}' \
		) \
		|| echo "Tag $${tag} not found" ; \
	done
endef

define pytest_helper
	@path="$(testdir)/$(1)" ; \
	if [[ -n "$(PYTEST_CUSTOM_PATH)" ]]; then path+="/$(PYTEST_CUSTOM_PATH)" ; fi ; \
		$(2) ; $(PYTEST) $(PYTEST_EXTRA_OPTS) $(PYTEST_OPTS) "$${path}"
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
	$(info PYTHON_VERSION_FILE -> `$(PYTHON_VERSION_FILE)`)
	$(info UV_VERSION -> `$(UV_VERSION)`)
	$(info UV_CACHE_DIR -> `$(UV_CACHE_DIR)`)
	$(info VIRTUALENV -> `$(VIRTUALENV)`)
	$(info UV_LOCKFILE -> `$(UV_LOCKFILE)`)
	$(info UV_CMD_OPTS -> `$(UV_CMD_OPTS)`)
	$(info UV_BUILD_OPTS -> `$(UV_BUILD_OPTS)`)

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

ifdef UV_BUILD_EXTRA_OPTS
	$(info UV_BUILD_EXTRA_OPTS -> `$(UV_BUILD_EXTRA_OPTS)`)
else
	$(info UV_BUILD_EXTRA_OPTS:)
	$(info ${\t}Use "--refresh" to refresh all cached data)
endif

ifdef INSTALL_EXTRAS
	$(info INSTALL_EXTRAS -> `$(INSTALL_EXTRAS)`)
endif

.PHONY: env-check-docker
# target: env-check-docker - Check the requirements for Docker
env-check-docker:
	@$(call which_helper,${DOCKER})

.PHONY: env-show-docker
# target: env-show-docker - Display the environment variables used to configure Docker
env-show-docker:
	$(info DOCKER_BUILD_PLATFORM -> `$(DOCKER_BUILD_PLATFORM)`)

	$(info DOCKER_PS_OPTS -> `$(DOCKER_PS_OPTS)`)
	$(info DOCKER_RM_OPTS -> `$(DOCKER_RM_OPTS)`)
	$(info DOCKER_SYSTEM_PRUNE_OPTS -> `$(DOCKER_SYSTEM_PRUNE_OPTS)`)
ifdef DOCKER_EXTRA_OPTS
	$(info DOCKER_EXTRA_OPTS -> `$(DOCKER_EXTRA_OPTS)`)
else
	$(info DOCKER_EXTRA_OPTS: Use "--progress=plain" to show container output)
endif

	$(info DOCKER_FILE -> `$(DOCKER_FILE)`)
	$(info DOCKER_COMPOSE_FILE -> `$(DOCKER_COMPOSE_FILE)`)
	$(info DOCKER_SERVICE_NAME -> `$(DOCKER_SERVICE_NAME)`)
	$(info DOCKER_IMAGE_NAME -> `$(DOCKER_IMAGE_NAME)`)
	$(info DOCKER_MOUNT_POINT -> `$(DOCKER_MOUNT_POINT)`)
	$(info DOCKER_CONTAINER_PORT -> `$(DOCKER_CONTAINER_PORT)`)
	$(info DOCKER_HOST_PORT -> `$(DOCKER_HOST_PORT)`)
	$(info DOCKER_COMMAND -> `$(DOCKER_COMMAND)`)

ifdef DOCKER_BUILD_ARGS
	$(info DOCKER_BUILD_ARGS -> `$(DOCKER_BUILD_ARGS)`)
endif
ifdef DOCKER_COMPOSE_EXPORTS
	$(info DOCKER_COMPOSE_EXPORTS -> `$(DOCKER_COMPOSE_EXPORTS)`)
endif

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
	$(info PYTEST_CUSTOM_PATH: Use "/path/to/test.py::TestClass::test_method" \
		to run a single test `test_method` from the suite `TestClass` of the \
		`test.py`)
endif

ifdef PYTEST_DEPLOYMENT
	$(info PYTEST_DEPLOYMENT -> `$(PYTEST_DEPLOYMENT)`)
else
	$(info PYTEST_DEPLOYMENT: Specify the deployed service URL, e.g., \
		"http://localhost:8000" for the local environment)
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

.PHONY: dist
# target: dist - Build Python packages
dist: env-check-python
# The default build strategy: build a source distribution ("sdist") from the
# source directory, and a binary distribution ("wheel") from the source
# distribution.
	@$(UV) build $(UV_CMD_OPTS) $(UV_BUILD_OPTS) $(UV_BUILD_EXTRA_OPTS) \
		"$(CURDIR)"

##
# Docker

.PHONY: docker-info
# target: docker-info - Show all images, containers, and volumes
docker-info: env-check-docker
	@$(DOCKER) images --all
	@echo
	@$(DOCKER) ps $(DOCKER_PS_OPTS)
	@echo
	@$(DOCKER) volume ls

.PHONY: docker-build
# target: docker-build - Build an image from the Dockerfile
docker-build: env-check-docker
	@$(DOCKER) buildx build --platform="$(DOCKER_BUILD_PLATFORM)" \
		$(DOCKER_EXTRA_OPTS) \
		$(DOCKER_BUILD_ARGS) \
		--file "$(DOCKER_FILE)" \
		--tag "$(DOCKER_IMAGE_NAME)" \
	"$(CURDIR)"

.PHONY: docker-run
# target: docker-run - Create and run a new container from an image (temporarily)
docker-run: env-check-docker
ifndef DOCKER_EXTRA_OPTS
	$(info DOCKER_EXTRA_OPTS: \
		Use "--publish 127.0.0.1:${DOCKER_HOST_PORT}:${DOCKER_CONTAINER_PORT}" \
		to bind port ${DOCKER_CONTAINER_PORT} of the container \
		to TCP port ${DOCKER_HOST_PORT} on 127.0.0.1 of the host)
endif
	@$(DOCKER) run \
		$(DOCKER_EXTRA_OPTS) \
		--interactive \
		--rm \
		--tty \
		--volume "$(CURDIR):$(DOCKER_MOUNT_POINT)" \
	"$(DOCKER_IMAGE_NAME)"

.PHONY: docker-compose
# target: docker-compose - Create and start containers, start any linked services
docker-compose: env-check-docker
	@$(DOCKER_COMPOSE_EXPORTS) ; \
	{ \
		$(DOCKER_COMPOSE) --file "$(DOCKER_COMPOSE_FILE)" up --build ; \
		$(DOCKER_COMPOSE) --file "$(DOCKER_COMPOSE_FILE)" down ; \
	}

.PHONY: docker-logs
# target: docker-logs - Follow and display logs from running containers
docker-logs: env-check-docker
	@$(DOCKER_COMPOSE_EXPORTS) ; \
		$(DOCKER_COMPOSE) --file "$(DOCKER_COMPOSE_FILE)" logs --follow

.PHONY: docker-shell
# target: docker-shell - Spawn a shell to the container
docker-shell: env-check-docker
	@$(DOCKER_COMPOSE_EXPORTS) ; $(DOCKER_COMPOSE) \
		--file "$(DOCKER_COMPOSE_FILE)" \
	exec "${DOCKER_SERVICE_NAME}" "${DOCKER_COMMAND}"

.PHONY: docker-clean
# target: docker-clean - Remove all images, containers, and volumes
docker-clean: env-check-docker
	@$(DOCKER) ps --all -q | xargs -r $(DOCKER) container rm $(DOCKER_RM_OPTS)
	@$(DOCKER) system prune $(DOCKER_SYSTEM_PRUNE_OPTS)

##
# Code quality

.PHONY: show-notes
# target: show-notes - List notes sorted by tag
show-notes: env-check
	$(call show_notes_helper, \
		${GIT} ls-files --cached --others --exclude-standard \
	)

.PHONY: show-notes-recent
# target: show-notes-recent - List notes from the GIT_DEPTH most recent commits and modified files
show-notes-recent: env-check
	$(call show_notes_helper, \
		{ \
			${GIT} log --no-merges --name-only --pretty=format: -n $(GIT_DEPTH) \
				| grep -v "^$$" ; \
			${GIT} diff --name-only ; \
			${GIT} diff --name-only --staged ; \
		} \
	)

.PHONY: check-deps
# target: check-deps - Find unused, missing, and transitive dependencies
check-deps: env-check-qa
	@(cd "$(CURDIR)" && $(DEPTRY) \
		"$(srcdir)" \
		"$(testdir)" \
	)

.PHONY: check-ruff
# target: check-ruff - Lint with Ruff
check-ruff: env-check-qa
	@$(RUFF) check "$(srcdir)" "$(testdir)"

.PHONY: check-mypy
# target: check-mypy - Perform static type checking with Mypy
check-mypy: env-check-qa
	@$(MYPY) $(MYPY_OPTS) "$(srcdir)" "$(testdir)"

.PHONY: check-pylint
# target: check-pylint - Perform code analysis with Pylint
check-pylint: env-check-qa
	@$(PYLINT) $(PYLINT_OPTS) "$(srcdir)" "$(testdir)"

.PHONY: lint
# target: lint - Run all available code analysis tools
lint: check-ruff check-mypy check-pylint

.PHONY: check-format
# target: check-format - Detect unformatted files
check-format: env-check-qa
	@$(RUFF) format --check "$(srcdir)" "$(testdir)"

.PHONY: format
# target: format - Format all discovered Python files
format: env-check-qa
	@$(RUFF) check --select I --fix "$(srcdir)" "$(testdir)"
	@$(RUFF) format "$(srcdir)" "$(testdir)"

.PHONY: test
# target: test - Run tests
test: env-check-qa
	$(call pytest_helper,${PYTEST_UNIT_DIR},:)

.PHONY: autotest
# target: autotest - Run system tests for the specified deployment
autotest: env-check-qa
ifndef PYTEST_DEPLOYMENT
	$(error PYTEST_DEPLOYMENT: URL of the deployed service is required, e.g., \
		"http://localhost:8000" for the local environment)
else
	$(info PYTEST_DEPLOYMENT -> `$(PYTEST_DEPLOYMENT)`)
endif
	$(call pytest_helper,${PYTEST_SYSTEM_DIR},${PYTEST_EXPORTS})

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
