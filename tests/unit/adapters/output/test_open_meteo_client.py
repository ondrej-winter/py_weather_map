"""Tests for the Open-Meteo output adapter."""

from datetime import date

import httpx

from weather_map.adapters.output.open_meteo.client import OpenMeteoHistoricalWeatherClient
from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.config import WeatherMapSettings
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import WeatherLayer


def test_open_meteo_client_parses_hourly_response() -> None:
    """The adapter should parse Open-Meteo hourly series into domain objects."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "hourly": {
                    "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                    "temperature_2m": [1.0, 2.5],
                }
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    adapter = OpenMeteoHistoricalWeatherClient(WeatherMapSettings(), client=client)

    result = adapter.fetch(
        HistoricalWeatherSampleRequest(
            locations=(GeoPoint(latitude=50.0, longitude=14.0),),
            layer=WeatherLayer.TEMPERATURE,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )
    )

    assert len(result) == 1
    assert result[0].values == (1.0, 2.5)
