from __future__ import annotations

from collections.abc import Callable, Iterator
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
def valid_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, valid_database_url: str
) -> None:
    """Supplies a valid database URL and an empty env file, isolated from `.env.local`."""
    empty_env_file = tmp_path / ".env.empty"
    empty_env_file.write_text("", encoding="utf-8")

    monkeypatch.setenv(f"{_PREFIX}ENV_FILE", str(empty_env_file))
    monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", valid_database_url)


class TestCheckDatabaseUrl:
    def test_accepts_valid_async_url(self, valid_database_url: str) -> None:
        value = SecretStr(valid_database_url)
        result = check_database_url(value)
        assert result is value
        assert result.get_secret_value() == valid_database_url

    def test_accepts_socket_host_via_query(
        self, make_database_url: Callable[..., str]
    ) -> None:
        url = make_database_url(host=None, query="?host=/var/run/postgresql")
        result = check_database_url(SecretStr(url))
        assert result.get_secret_value() == url

    def test_rejects_unparseable_url(self) -> None:
        with pytest.raises(ValueError, match="invalid database URL"):
            check_database_url(SecretStr("not/a/valid/url"))

    @pytest.mark.parametrize(
        "driver",
        ["postgresql", "postgresql+psycopg", "mysql+aiomysql"],
    )
    def test_rejects_wrong_driver(
        self, make_database_url: Callable[..., str], driver: str
    ) -> None:
        url = make_database_url(driver=driver)
        with pytest.raises(ValueError, match="driver"):
            check_database_url(SecretStr(url))

    def test_rejects_missing_host(self, make_database_url: Callable[..., str]) -> None:
        with pytest.raises(ValueError, match="host or socket"):
            check_database_url(SecretStr(make_database_url(host=None)))

    def test_rejects_missing_database_name(
        self, make_database_url: Callable[..., str]
    ) -> None:
        with pytest.raises(ValueError, match="database name"):
            check_database_url(SecretStr(make_database_url(database=None)))


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
    def test_applies_logging_defaults(self, valid_database_url: str) -> None:
        settings = Settings(DATABASE_URL=SecretStr(valid_database_url), _env_file=None)
        assert settings.LOG_LEVEL == "DEBUG"
        assert settings.LOG_FORMAT == "console"
        assert settings.LOG_COLORS is True
        assert settings.LOG_VERBOSE is False

    def test_masks_database_url(
        self, valid_database_url: str, database_password: str
    ) -> None:
        settings = Settings(DATABASE_URL=SecretStr(valid_database_url), _env_file=None)
        masked = str(settings.DATABASE_URL)
        assert settings.DATABASE_URL == SecretStr(valid_database_url)
        assert masked and set(masked) == {"*"}
        assert database_password not in repr(settings.DATABASE_URL)

    def test_requires_database_url(self) -> None:
        with pytest.raises(ValidationError, match="DATABASE_URL"):
            Settings(_env_file=None)

    def test_rejects_invalid_log_level(self, valid_database_url: str) -> None:
        with pytest.raises(ValidationError, match="LOG_LEVEL"):
            Settings(
                LOG_LEVEL="bogus",
                DATABASE_URL=SecretStr(valid_database_url),
                _env_file=None,
            )

    def test_does_not_leak_secret_in_validation_errors(
        self, make_database_url: Callable[..., str]
    ) -> None:
        secret_password = "sup3r-secret"
        url = make_database_url(driver="postgresql", password=secret_password)
        with pytest.raises(ValidationError) as excinfo:
            Settings(DATABASE_URL=SecretStr(url), _env_file=None)
        assert secret_password not in str(excinfo.value)


class TestSettingsEnvironment:
    def test_reads_values_from_environment(
        self, monkeypatch: pytest.MonkeyPatch, valid_database_url: str
    ) -> None:
        monkeypatch.setenv(f"{_PREFIX}LOG_LEVEL", "info")
        monkeypatch.setenv(f"{_PREFIX}LOG_VERBOSE", "true")
        monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", valid_database_url)

        settings = Settings(_env_file=None)
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LOG_VERBOSE is True
        assert settings.DATABASE_URL == SecretStr(valid_database_url)

    def test_ignores_lowercased_field_names(
        self, monkeypatch: pytest.MonkeyPatch, valid_database_url: str
    ) -> None:
        monkeypatch.setenv(f"{_PREFIX}log_level", "info")
        monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", valid_database_url)

        settings = Settings(_env_file=None)
        assert settings.LOG_LEVEL == "DEBUG"

    def test_ignores_unprefixed_variables(
        self, monkeypatch: pytest.MonkeyPatch, valid_database_url: str
    ) -> None:
        monkeypatch.setenv("LOG_LEVEL", "info")
        monkeypatch.setenv(f"{_PREFIX}DATABASE_URL", valid_database_url)

        settings = Settings(_env_file=None)
        assert settings.LOG_LEVEL == "DEBUG"

    def test_forbids_unknown_fields(self, valid_database_url: str) -> None:
        data = {"DATABASE_URL": valid_database_url, "NONEXISTENT": "x"}
        with pytest.raises(ValidationError, match="NONEXISTENT"):
            Settings.model_validate(data)

    def test_reads_values_from_env_file(
        self, tmp_path: Path, valid_database_url: str
    ) -> None:
        env_file = tmp_path / ".env.settings"
        env_file.write_text(
            f"{_PREFIX}LOG_LEVEL=warning\n{_PREFIX}DATABASE_URL={valid_database_url}\n",
            encoding="utf-8",
        )

        settings = Settings(_env_file=str(env_file))
        assert settings.LOG_LEVEL == "WARNING"
        assert settings.DATABASE_URL == SecretStr(valid_database_url)


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
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, valid_database_url: str
    ) -> None:
        env_file = tmp_path / ".env.override"
        env_file.write_text(
            f"{_PREFIX}LOG_LEVEL=warning\n{_PREFIX}DATABASE_URL={valid_database_url}\n",
            encoding="utf-8",
        )
        monkeypatch.setenv(f"{_PREFIX}ENV_FILE", str(env_file))
        monkeypatch.delenv(f"{_PREFIX}DATABASE_URL", raising=False)

        settings = get_settings(reload=True)
        assert settings.LOG_LEVEL == "WARNING"
        assert settings.DATABASE_URL == SecretStr(valid_database_url)
