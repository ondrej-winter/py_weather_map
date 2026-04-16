"""Tests for available weather layer metadata."""

from weather_map.application.use_cases.get_available_layers import GetAvailableWeatherLayersUseCase


def test_get_available_layers_returns_all_supported_layers() -> None:
    """The layer metadata use case should expose the configured layers."""
    use_case = GetAvailableWeatherLayersUseCase()

    result = use_case.execute()

    assert {option.layer.value for option in result} == {
        "temperature",
        "precipitation",
        "humidity",
        "wind_speed",
    }
