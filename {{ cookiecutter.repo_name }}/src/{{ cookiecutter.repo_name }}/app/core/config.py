from functools import lru_cache
from os import getenv
from typing import Annotated, get_args

from pydantic import AfterValidator, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import make_url as sa_make_url
from sqlalchemy.exc import ArgumentError

from {{ cookiecutter.repo_name }}.logging import LogFormatT, check_log_level

__all__ = [
    "DEFAULT_LOCAL_ENV_FILE",
    "Settings",
    "get_settings",
]


DEFAULT_LOCAL_ENV_FILE = ".env.local"

DATABASE_DRIVER = "postgresql+asyncpg"


def check_database_url(value: SecretStr) -> SecretStr:
    """Validates a database URL for the SQLAlchemy driver.

    Error messages never quote the URL, which can hold a password.

    Args:
        value: Database URL to validate.

    Returns:
        The input value unchanged.

    Raises:
        ValueError: If the URL cannot be parsed, uses a driver other than
            `DATABASE_DRIVER`, has neither a host nor a socket directory, or lacks a
            database name.
    """
    _url = value.get_secret_value()
    try:
        url = sa_make_url(_url)
    except ArgumentError, ValueError:
        # The error for a malformed port quotes URL text that can include the password.
        raise ValueError("invalid database URL") from None

    driver = url.drivername
    if driver != DATABASE_DRIVER:
        raise ValueError(
            f"database URL must use `{DATABASE_DRIVER}` driver, not `{driver}`"
        )

    if not (url.host or url.query.get("host")):
        raise ValueError("database URL must include a host or socket directory")

    # A URL that ends in a bare slash parses to an empty name rather than None.
    if not url.database:
        raise ValueError("database URL must include a database name")

    return value


def _resolve_env_file() -> str:
    return getenv("{{ cookiecutter.env_prefix }}ENV_FILE") or DEFAULT_LOCAL_ENV_FILE


LogLevel = Annotated[str, AfterValidator(check_log_level)]

DatabaseURL = Annotated[SecretStr, AfterValidator(check_database_url)]


class Settings(BaseSettings):
    """Service settings read from environment variables and an environment file.

    Each field reads the environment variable of the same name with the
    `SettingsConfigDict["env_prefix"]` prefix. Environment variables take precedence
    over the environment file.

    Obtain instances through `get_settings()`, which caches them.
    """

    ##
    # Logging

    LOG_LEVEL: LogLevel = Field("debug", description="Root logger level")
    LOG_FORMAT: LogFormatT = Field(
        "console",
        description=f"Logging output format: {', '.join(get_args(LogFormatT))}",
    )
    LOG_COLORS: bool = Field(True, description="Colorize console output on a TTY")
    LOG_VERBOSE: bool = Field(False, description="Enable verbose logs")

    ##
    # Database

    DATABASE_URL: DatabaseURL = Field(
        ..., description="URL used to connect to a database"
    )

    model_config = SettingsConfigDict(
        # Keep raw values out of validation errors.
        hide_input_in_errors=True,
        # Reject unknown initialization arguments and environment file entries. Unknown
        # environment variables are ignored, not rejected.
        extra="forbid",
        # Whether environment and CLI variable names should be read with
        # case-sensitivity.
        case_sensitive=True,
        # Whether to allow partial updates on nested model default object fields.
        nested_model_default_partial_update=False,
        # Prefix for all environment variables.
        env_prefix="{{ cookiecutter.env_prefix }}",
        # Resolved at import time and used only when `Settings` is instantiated
        # directly; `get_settings()` resolves the environment file on its first call and
        # on reload.
        env_file=_resolve_env_file(),
        # The environment file encoding.
        env_file_encoding="utf-8",
        # Read an empty value as an empty string instead of falling back to the field
        # default.
        env_ignore_empty=False,
        # The nested env values delimiter.
        env_nested_delimiter="__",
        # The env string value that should be parsed (e.g. "null", "void", "None", etc.)
        # into `None`.
        env_parse_none_str=None,  # <- no parsing should occur
        # Parse enum field names to values.
        env_parse_enums=None,  # <- no parsing should occur
        # The secret files directory or a sequence of directories.
        secrets_dir=None,
    )


@lru_cache(maxsize=1)
def _get_settings() -> Settings:
    return Settings(_env_file=_resolve_env_file())


def get_settings(*, reload: bool = False) -> Settings:
    """Returns the cached settings singleton.

    Args:
        reload: If `True`, discard the cached instance and rebuild it from the
            environment and env file before returning.

    Raises:
        pydantic.ValidationError: If a required setting is missing or a setting is
            invalid.
    """
    if reload:
        _get_settings.cache_clear()

    return _get_settings()
