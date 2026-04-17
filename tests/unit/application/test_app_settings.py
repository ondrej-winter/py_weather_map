"""Tests for the application-facing settings DTO."""

from pathlib import Path

import pytest

from weather_map.application.dtos import WeatherMapSettings


def test_weather_map_settings_uses_project_defaults() -> None:
    """The settings DTO should expose the canonical default values."""
    settings = WeatherMapSettings()

    assert settings.openmeteo_base_url == "https://archive-api.open-meteo.com/v1/archive"
    assert settings.request_timeout_seconds == 15.0
    assert settings.local_weather_data_directory == Path("data/weather_history")
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert settings.default_grid_rows == 8
    assert settings.default_grid_columns == 8
    assert settings.max_grid_rows == 20
    assert settings.max_grid_columns == 20


def test_weather_map_settings_preserves_explicit_overrides() -> None:
    """Explicit DTO values should override defaults."""
    settings = WeatherMapSettings(
        request_timeout_seconds=30.0,
        local_weather_data_directory=Path("custom-data"),
        port=9000,
        default_grid_rows=10,
        default_grid_columns=12,
        max_grid_rows=24,
        max_grid_columns=24,
    )

    assert settings.request_timeout_seconds == 30.0
    assert settings.local_weather_data_directory == Path("custom-data")
    assert settings.port == 9000
    assert settings.default_grid_rows == 10
    assert settings.default_grid_columns == 12
    assert settings.max_grid_rows == 24
    assert settings.max_grid_columns == 24


def test_weather_map_settings_rejects_non_positive_timeout() -> None:
    """The DTO should reject non-positive request timeouts."""
    with pytest.raises(ValueError, match="request_timeout_seconds must be positive"):
        WeatherMapSettings(request_timeout_seconds=0.0)


def test_weather_map_settings_rejects_negative_coordinate_precision() -> None:
    """The DTO should reject negative coordinate precision."""
    with pytest.raises(ValueError, match="local_weather_coordinate_precision must be non-negative"):
        WeatherMapSettings(local_weather_coordinate_precision=-1)


def test_weather_map_settings_rejects_blank_host() -> None:
    """The DTO should reject a blank host value."""
    with pytest.raises(ValueError, match="host must not be blank"):
        WeatherMapSettings(host="   ")


def test_weather_map_settings_rejects_out_of_range_port() -> None:
    """The DTO should reject ports outside the allowed range."""
    with pytest.raises(ValueError, match="port must be between 1 and 65535"):
        WeatherMapSettings(port=70000)
