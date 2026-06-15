from {{ cookiecutter.repo_name }} import (
    get_logger,
    get_settings,
    is_level_enabled,
    setup_logging,
)
from {{ cookiecutter.repo_name }}.app import (
    __project_name__,
    __version__,
)

logger = get_logger(__name__)


def main() -> None:
    settings = get_settings()
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        enable_colors=settings.LOG_COLORS,
    )

    if is_level_enabled(logger):
        logger.debug("%r", settings)

    _verbose = settings.LOG_VERBOSE

    logger.info("Welcome to %s version %s", __project_name__, __version__)
