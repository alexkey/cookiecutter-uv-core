# The re-exports are lazy because every CLI invocation imports this package.
lazy from {{ cookiecutter.repo_name }}.app.core.config import get_settings
lazy from {{ cookiecutter.repo_name }}.logging import (
    get_logger,
    is_level_enabled,
    setup_logging,
)

__all__ = [
    "get_logger",
    "get_settings",
    "is_level_enabled",
    "setup_logging",
]
