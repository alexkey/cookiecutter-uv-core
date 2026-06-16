from __future__ import annotations

import os
import random

import pytest

PYTEST_MARK_SLOW = "slow"
PYTEST_OPT_SKIP_SLOW = "--skip-slow"

SEED_ENV_VAR = "{{ cookiecutter.env_prefix }}TEST_SEED"

_seed_key = pytest.StashKey[int]()


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        PYTEST_OPT_SKIP_SLOW, action="store_true", default=False, help="skip slow tests"
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        f"{PYTEST_MARK_SLOW}: marks tests as slow (deselect with `{PYTEST_OPT_SKIP_SLOW}`)",
    )

    seed_value = os.environ.get(SEED_ENV_VAR)
    if seed_value:
        try:
            seed = int(seed_value)
        except ValueError:
            raise pytest.UsageError(
                f"{SEED_ENV_VAR} must be an integer, got {seed_value!r}"
            ) from None
    else:
        seed = random.SystemRandom().randrange(2**32)

    config.stash[_seed_key] = seed


def pytest_report_header(config: pytest.Config) -> str:
    return f"random seed: {config.stash[_seed_key]} (set {SEED_ENV_VAR} to reproduce)"


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    markers_to_skip = {
        PYTEST_MARK_SLOW: (
            config.getoption(PYTEST_OPT_SKIP_SLOW),
            f"skipping slow tests as {PYTEST_OPT_SKIP_SLOW} is set",
        ),
    }

    for item in items:
        for marker, (condition, reason) in markers_to_skip.items():
            if condition and marker in item.keywords:
                item.add_marker(pytest.mark.skip(reason=reason))


@pytest.fixture(scope="session")
def rng(pytestconfig: pytest.Config) -> random.Random:
    """A deterministic pseudo-random generator shared across the test session."""
    return random.Random(pytestconfig.stash[_seed_key])
