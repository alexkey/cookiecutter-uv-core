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
    "get_settings",
]


DEFAULT_LOCAL_ENV_FILE = ".env.local"

DATABASE_DRIVER = "postgresql+asyncpg"


def check_database_url(value: SecretStr) -> SecretStr:
    raw = value.get_secret_value()
    try:
        url = sa_make_url(raw)
    except ArgumentError as exc:
        raise ValueError(f"invalid database URL: {value!r}") from exc

    driver = getattr(url, "drivername", "")
    if driver.lower() != DATABASE_DRIVER:
        raise ValueError(
            f"database URL must use `{DATABASE_DRIVER}` driver, not `{driver}`"
        )

    if url.host is None or url.database is None:
        raise ValueError("database URL must include host and database name")

    return value


LogLevel = Annotated[str, AfterValidator(check_log_level)]

DatabaseURL = Annotated[SecretStr, AfterValidator(check_database_url)]


class Settings(BaseSettings):
    ##
    # Logging

    LOG_LEVEL: LogLevel = Field("debug", description="Root logger level")
    LOG_FORMAT: LogFormatT = Field(
        "console",
        description=f"Logging output format {', '.join(get_args(LogFormatT))}",
    )
    LOG_COLORS: bool = Field(True, description="Use colors for a nicer output")
    LOG_VERBOSE: bool = Field(False, description="Enable verbose logs")

    ##
    # Database

    DATABASE_URL: DatabaseURL = Field(
        ..., description="URL used to connect to a database"
    )

    model_config = SettingsConfigDict(
        # Forbid extra attributes during model initialization.
        extra="forbid",
        # Whether environment and CLI variable names should be read with
        # case-sensitivity.
        case_sensitive=True,
        # Whether to allow partial updates on nested model default object fields.
        nested_model_default_partial_update=False,
        # Prefix for all environment variables.
        env_prefix="{{ cookiecutter.env_prefix }}",
        # The env file(s) to load settings values from; None indicates that environment
        # variables should not be loaded from an env file.
        env_file=(getenv("{{ cookiecutter.env_prefix }}ENV_FILE") or DEFAULT_LOCAL_ENV_FILE),
        # The env file encoding.
        env_file_encoding="utf-8",
        # Ignore environment variables where the value is an empty string.
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
    return Settings()


def get_settings(*, reload: bool = False) -> Settings:
    if reload:
        _get_settings.cache_clear()

    return _get_settings()
