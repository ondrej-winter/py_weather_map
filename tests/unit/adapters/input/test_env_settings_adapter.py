"""Tests for the environment settings adapter."""

from pathlib import Path

import pytest

from weather_map.adapters.input.env_settings_adapter import EnvSettingsAdapter
from weather_map.application.exceptions import ConfigurationError


def test_env_settings_adapter_uses_dto_defaults_when_env_is_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unset optional env vars should allow application defaults to apply."""
    _clear_weather_map_env(monkeypatch)

    settings = EnvSettingsAdapter().load()

    assert settings.openmeteo_base_url == "https://archive-api.open-meteo.com/v1/archive"
    assert settings.request_timeout_seconds == 15.0
    assert settings.local_weather_data_directory == Path("data/weather_history")
    assert settings.port == 8000


def test_env_settings_adapter_overrides_defaults_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Configured env vars should override DTO defaults after normalization."""
    _clear_weather_map_env(monkeypatch)
    monkeypatch.setenv("WEATHER_MAP_OPENMETEO_BASE_URL", "  https://example.test/archive  ")
    monkeypatch.setenv("WEATHER_MAP_REQUEST_TIMEOUT_SECONDS", "20.5")
    monkeypatch.setenv("WEATHER_MAP_LOCAL_WEATHER_DATA_DIRECTORY", "custom/weather")
    monkeypatch.setenv("WEATHER_MAP_PORT", "9001")
    monkeypatch.setenv("WEATHER_MAP_DEFAULT_GRID_ROWS", "9")
    monkeypatch.setenv("WEATHER_MAP_DEFAULT_GRID_COLUMNS", "10")
    monkeypatch.setenv("WEATHER_MAP_MAX_GRID_ROWS", "30")
    monkeypatch.setenv("WEATHER_MAP_MAX_GRID_COLUMNS", "31")

    settings = EnvSettingsAdapter().load()

    assert settings.openmeteo_base_url == "https://example.test/archive"
    assert settings.request_timeout_seconds == 20.5
    assert settings.local_weather_data_directory == Path("custom/weather")
    assert settings.port == 9001
    assert settings.default_grid_rows == 9
    assert settings.default_grid_columns == 10
    assert settings.max_grid_rows == 30
    assert settings.max_grid_columns == 31


def test_env_settings_adapter_rejects_blank_text_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Blank text env vars should raise a configuration error."""
    _clear_weather_map_env(monkeypatch)
    monkeypatch.setenv("WEATHER_MAP_HOST", "   ")

    with pytest.raises(ConfigurationError, match="Invalid configuration"):
        EnvSettingsAdapter().load()


def test_env_settings_adapter_rejects_invalid_numeric_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Out-of-range numeric env vars should raise a configuration error."""
    _clear_weather_map_env(monkeypatch)
    monkeypatch.setenv("WEATHER_MAP_DEFAULT_GRID_ROWS", "9")
    monkeypatch.setenv("WEATHER_MAP_MAX_GRID_ROWS", "8")

    with pytest.raises(
        ConfigurationError,
        match="WEATHER_MAP_MAX_GRID_ROWS must be greater than or equal to WEATHER_MAP_DEFAULT_GRID_ROWS",
    ):
        EnvSettingsAdapter().load()


def _clear_weather_map_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove weather-map env vars so tests stay isolated from developer state."""
    for name in (
        "WEATHER_MAP_OPENMETEO_BASE_URL",
        "WEATHER_MAP_REQUEST_TIMEOUT_SECONDS",
        "WEATHER_MAP_LOCAL_WEATHER_DATA_DIRECTORY",
        "WEATHER_MAP_LOCAL_WEATHER_COORDINATE_PRECISION",
        "WEATHER_MAP_HOST",
        "WEATHER_MAP_PORT",
        "WEATHER_MAP_DEFAULT_GRID_ROWS",
        "WEATHER_MAP_DEFAULT_GRID_COLUMNS",
        "WEATHER_MAP_MAX_GRID_ROWS",
        "WEATHER_MAP_MAX_GRID_COLUMNS",
    ):
        monkeypatch.delenv(name, raising=False)
