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
		grep "__version__" "${srcdir}/{{ cookiecutter.repo_name }}/app/__init__.py" \
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

UV_LOCKFILE = $(CURDIR)/uv.lock
VIRTUALENV = $(if \
	${UV_PROJECT_ENVIRONMENT},${UV_PROJECT_ENVIRONMENT},${CURDIR}/.venv)

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
export DOCKER_SERVICE_PORT="$(DOCKER_SERVICE_PORT)"
export DOCKER_CONTAINER_PORT="$(DOCKER_CONTAINER_PORT)" ; \
endef


#---
# Targets
#---

all:
	@echo "$(PACKAGE_NAME) $(PACKAGE_VERSION) ($(OS) @ $(MACHINE) [$(VIRTUALENV)])"
	@echo "Type \`make help\` for a list of available targets"

.PHONY: env-check
# Check the local environment for requirements
env-check:
ifdef _install_hints
	$(info ${_install_hints})
endif
	@$(call which_helper,${SED})
	@$(call which_helper,${GREP})
	@$(call which_helper,${GIT})

.PHONY: env-check-python
# Check the requirements for Python
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

.PHONY: env-check-lockfile
# Ensure the lockfile exists
env-check-lockfile:
ifeq ($(wildcard ${UV_LOCKFILE}),)
	$(error The project lockfile does not exist: `${UV_LOCKFILE}`)
endif
	$(info Requires that the project lockfile (`uv.lock`) is up-to-date. \
		If the lockfile is needs to be updated, the target will exit with an \
		error \
	)

.PHONY: env-check-venv
# Ensure the virtual environment exists
env-check-venv:
ifeq ($(wildcard ${VIRTUALENV}),)
	$(error The virtual environment is missing at the target path: \
		`${VIRTUALENV}`)
endif

.PHONY: env-check-docker
# Check the requirements for Docker
env-check-docker:
	@$(call which_helper,${DOCKER})


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
