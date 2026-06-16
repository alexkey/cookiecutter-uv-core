from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError

from {{ cookiecutter.repo_name }}.app.core.config import (
    DEFAULT_LOCAL_ENV_FILE,
    Settings,
    _get_settings,
    _resolve_env_file,
    check_database_url,
    get_settings,
)

_PREFIX = "{{ cookiecutter.env_prefix }}"

_CONFIG_ENV_VARS = (
    f"{_PREFIX}LOG_LEVEL",
    f"{_PREFIX}LOG_FORMAT",
    f"{_PREFIX}LOG_COLORS",
    f"{_PREFIX}LOG_VERBOSE",
    f"{_PREFIX}DATABASE_URL",
    f"{_PREFIX}ENV_FILE",
)

_PASSWORD = "passwd"


def _database_url(
    *,
    driver: str = "postgresql+asyncpg",
    user: str = "user",
    password: str = _PASSWORD,
    host: str | None = "host",
    port: int | None = 5432,
    database: str | None = "db",
    query: str = "",
) -> str:
    if host is None:
        authority = ""
    else:
        authority = f"{host}:{port}" if port is not None else host
    path = f"/{database}" if database is not None else ""

    return f"{driver}://{user}:{password}@{authority}{path}{query}"


VALID_DATABASE_URL = _database_url()


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Removes config env vars and clears the cached singleton around every test."""
    for name in _CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    _get_settings.cache_clear()
    try:
        yield
    finally:
        _get_settings.cache_clear()


@pytest.fixture
def valid_environment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Supplies a valid database URL and an empty env file, isolated from `.env.local`."""
    empty_env_file = tmp_path / ".env.empty"
    empty_env_file.write_text("", encoding="utf-8")

    monkeypatch.setenv(f"{_PREFIX}ENV_FILE", str(empty_env_file))
    monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", VALID_DATABASE_URL)


class TestCheckDatabaseUrl:
    def test_accepts_valid_async_url(self) -> None:
        value = SecretStr(VALID_DATABASE_URL)
        result = check_database_url(value)
        assert result is value
        assert result.get_secret_value() == VALID_DATABASE_URL

    def test_accepts_socket_host_via_query(self) -> None:
        url = _database_url(host=None, query="?host=/var/run/postgresql")
        result = check_database_url(SecretStr(url))
        assert result.get_secret_value() == url

    def test_rejects_unparseable_url(self) -> None:
        with pytest.raises(ValueError, match="invalid database URL"):
            check_database_url(SecretStr("not/a/valid/url"))

    @pytest.mark.parametrize(
        "driver",
        ["postgresql", "postgresql+psycopg", "mysql+aiomysql"],
    )
    def test_rejects_wrong_driver(self, driver: str) -> None:
        url = _database_url(driver=driver)
        with pytest.raises(ValueError, match="driver"):
            check_database_url(SecretStr(url))

    def test_rejects_missing_host(self) -> None:
        with pytest.raises(ValueError, match="host or socket"):
            check_database_url(SecretStr(_database_url(host=None)))

    def test_rejects_missing_database_name(self) -> None:
        with pytest.raises(ValueError, match="database name"):
            check_database_url(SecretStr(_database_url(database=None)))


class TestResolveEnvFile:
    def test_defaults_to_local_env_file(self) -> None:
        assert _resolve_env_file() == DEFAULT_LOCAL_ENV_FILE

    def test_uses_override_when_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(f"{_PREFIX}ENV_FILE", ".env.custom")
        assert _resolve_env_file() == ".env.custom"

    def test_falls_back_when_override_is_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(f"{_PREFIX}ENV_FILE", "")
        assert _resolve_env_file() == DEFAULT_LOCAL_ENV_FILE


class TestSettingsDefaults:
    def test_applies_logging_defaults(self) -> None:
        settings = Settings(DATABASE_URL=SecretStr(VALID_DATABASE_URL), _env_file=None)
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.LOG_FORMAT == "console"
        assert settings.LOG_COLORS is True
        assert settings.LOG_VERBOSE is False

    def test_database_url_is_secret(self) -> None:
        settings = Settings(DATABASE_URL=SecretStr(VALID_DATABASE_URL), _env_file=None)
        masked = str(settings.DATABASE_URL)
        assert settings.DATABASE_URL == SecretStr(VALID_DATABASE_URL)
        assert masked and set(masked) == {"*"}
        assert _PASSWORD not in repr(settings.DATABASE_URL)

    def test_requires_database_url(self) -> None:
        with pytest.raises(ValidationError, match="DATABASE_URL"):
            Settings(_env_file=None)

    def test_rejects_invalid_log_level(self) -> None:
        with pytest.raises(ValidationError, match="LOG_LEVEL"):
            Settings(
                LOG_LEVEL="bogus",
                DATABASE_URL=SecretStr(VALID_DATABASE_URL),
                _env_file=None,
            )

    def test_does_not_leak_secret_in_validation_errors(self) -> None:
        secret_password = "sup3r-secret"
        url = _database_url(driver="postgresql", password=secret_password)
        with pytest.raises(ValidationError) as excinfo:
            Settings(DATABASE_URL=SecretStr(url), _env_file=None)
        assert secret_password not in str(excinfo.value)


class TestSettingsEnvironment:
    def test_reads_values_from_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(f"{_PREFIX}LOG_LEVEL", "info")
        monkeypatch.setenv(f"{_PREFIX}LOG_VERBOSE", "true")
        monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", VALID_DATABASE_URL)

        settings = Settings(_env_file=None)
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LOG_VERBOSE is True
        assert settings.DATABASE_URL == SecretStr(VALID_DATABASE_URL)

    def test_is_case_sensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(f"{_PREFIX}log_level", "info")
        monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", VALID_DATABASE_URL)

        settings = Settings(_env_file=None)
        assert settings.LOG_LEVEL == "DEBUG"

    def test_ignores_unprefixed_variables(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("LOG_LEVEL", "info")
        monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", VALID_DATABASE_URL)

        settings = Settings(_env_file=None)
        assert settings.LOG_LEVEL == "DEBUG"

    def test_forbids_unknown_fields(self) -> None:
        data = {"DATABASE_URL": VALID_DATABASE_URL, "NONEXISTENT": "x"}
        with pytest.raises(ValidationError, match="NONEXISTENT"):
            Settings.model_validate(data)

    def test_reads_values_from_env_file(self, tmp_path: Path) -> None:
        env_file = tmp_path / ".env.settings"
        env_file.write_text(
            f"{_PREFIX}LOG_LEVEL=warning\n{_PREFIX}DATABASE_URL={VALID_DATABASE_URL}\n",
            encoding="utf-8",
        )

        settings = Settings(_env_file=str(env_file))
        assert settings.LOG_LEVEL == "WARNING"
        assert settings.DATABASE_URL == SecretStr(VALID_DATABASE_URL)


@pytest.mark.usefixtures("valid_environment")
class TestGetSettings:
    def test_returns_cached_singleton(self) -> None:
        assert get_settings() is get_settings()

    def test_reload_rebuilds_instance(self) -> None:
        first = get_settings()
        second = get_settings(reload=True)
        assert first is not second

    def test_reload_picks_up_changed_environment(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(f"{_PREFIX}LOG_LEVEL", "info")
        assert get_settings(reload=True).LOG_LEVEL == "INFO"

        monkeypatch.setenv(f"{_PREFIX}LOG_LEVEL", "warning")
        assert get_settings().LOG_LEVEL == "INFO"
        assert get_settings(reload=True).LOG_LEVEL == "WARNING"

    def test_reload_honors_env_file_override(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        env_file = tmp_path / ".env.override"
        env_file.write_text(
            f"{_PREFIX}LOG_LEVEL=warning\n{_PREFIX}DATABASE_URL={VALID_DATABASE_URL}\n",
            encoding="utf-8",
        )
        monkeypatch.setenv(f"{_PREFIX}ENV_FILE", str(env_file))
        monkeypatch.delenv(f"{_PREFIX}DATABASE_URL", raising=False)

        settings = get_settings(reload=True)
        assert settings.LOG_LEVEL == "WARNING"
        assert settings.DATABASE_URL == SecretStr(VALID_DATABASE_URL)
