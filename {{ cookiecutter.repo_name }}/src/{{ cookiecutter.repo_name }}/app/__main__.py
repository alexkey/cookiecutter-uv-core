from {{ cookiecutter.repo_name }} import (
    get_logger,
    get_settings,
    is_level_enabled,
)
from {{ cookiecutter.repo_name }}.app import (
    __project_name__,
    __version__,
)

logger = get_logger(__name__)
settings = get_settings()


def main() -> None:
    if is_level_enabled(logger):
        logger.debug("%r", settings)

    _verbose = settings.LOG_VERBOSE

    logger.info(f"Welcome to {__project_name__} version {__version__}")
