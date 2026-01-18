from {{ cookiecutter.repo_name }}.app.core.config import get_settings
from {{ cookiecutter.repo_name }}.logging import (
    get_logger,
    is_level_enabled,
    setup_logging,
)

__all__ = [
    "get_logger",
    "get_settings",
    "is_level_enabled",
]


settings = get_settings()

setup_logging(
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT,
    enable_colors=settings.LOG_COLORS,
)
