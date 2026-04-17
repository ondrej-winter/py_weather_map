"""Tests for the application-level Open-Meteo historical weather provider."""

from datetime import date, datetime, timezone

from weather_map.adapters.output.open_meteo import (
    OpenMeteoArchiveLocationData,
    OpenMeteoArchiveRequest,
    OpenMeteoHistoricalWeatherProvider,
    OpenMeteoHourlyData,
    OpenMeteoHourlyVariable,
)
from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import WeatherLayer


class FakeArchivePort:
    """Fake Open-Meteo archive port for deterministic provider tests."""

    def __init__(self, result: list[OpenMeteoArchiveLocationData]) -> None:
        self.result = result
        self.requests: list[OpenMeteoArchiveRequest] = []

    def fetch_archive(self, request: OpenMeteoArchiveRequest) -> list[OpenMeteoArchiveLocationData]:
        self.requests.append(request)
        return self.result


def test_open_meteo_historical_weather_provider_maps_layer_to_hourly_variable() -> None:
    """The provider should translate weather-layer intent into an Open-Meteo archive request."""
    location = GeoPoint(latitude=50.0, longitude=14.0)
    archive_port = FakeArchivePort(
        result=[
            OpenMeteoArchiveLocationData(
                location=location,
                hourly=OpenMeteoHourlyData(
                    timestamps_utc=(datetime(2024, 1, 1, 0, tzinfo=timezone.utc),),
                    values_by_variable={OpenMeteoHourlyVariable.TEMPERATURE_2M: (1.5,)},
                ),
            )
        ]
    )
    provider = OpenMeteoHistoricalWeatherProvider(client=archive_port)

    result = provider.fetch(
        HistoricalWeatherSampleRequest(
            locations=(location,),
            layer=WeatherLayer.TEMPERATURE,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )
    )

    assert len(archive_port.requests) == 1
    assert archive_port.requests[0].hourly_variables == (OpenMeteoHourlyVariable.TEMPERATURE_2M,)
    assert result[0].location == location
    assert result[0].values == (1.5,)
