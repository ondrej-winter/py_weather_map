"""Integration tests for the application bootstrap and HTTP endpoints."""

from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from weather_map.adapters.input.http.app import create_app
from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.application.use_cases.get_available_layers import GetAvailableWeatherLayersUseCase
from weather_map.application.use_cases.get_weather_heatmap import GetWeatherHeatmapUseCase
from weather_map.config import WeatherMapSettings
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import LocationWeatherSeries


class FakeProvider:
    """Integration fake provider returning deterministic values."""

    def fetch(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        return [
            LocationWeatherSeries(
                location=GeoPoint(latitude=location.latitude, longitude=location.longitude),
                timestamps_utc=(datetime(2024, 1, 1, 12, tzinfo=timezone.utc),),
                values=(float(index + 1),),
            )
            for index, location in enumerate(request.locations)
        ]


class FakeCache:
    """Integration fake cache storing the last value."""

    def __init__(self) -> None:
        self._data: list[LocationWeatherSeries] | None = None

    def get(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries] | None:
        return self._data

    def set(self, request: HistoricalWeatherSampleRequest, series: list[LocationWeatherSeries]) -> None:
        self._data = series


def test_heatmap_endpoint_returns_grid_samples() -> None:
    """The wired app should return a non-empty heatmap response."""
    heatmap_use_case = GetWeatherHeatmapUseCase(provider=FakeProvider(), cache=FakeCache())
    app = create_app(heatmap_use_case, GetAvailableWeatherLayersUseCase(), WeatherMapSettings())
    client = TestClient(app)

    response = client.get(
        "/api/heatmap",
        params={
            "north": 50.0,
            "south": 49.0,
            "east": 15.0,
            "west": 14.0,
            "layer": "temperature",
            "mode": "snapshot",
            "start_date": date(2024, 1, 1).isoformat(),
            "end_date": date(2024, 1, 1).isoformat(),
            "snapshot_hour": 12,
            "grid_rows": 2,
            "grid_columns": 2,
        },
    )

    assert response.status_code == 200
    assert response.json()["sample_count"] == 4
