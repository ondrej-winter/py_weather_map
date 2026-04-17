"""Tests for the Open-Meteo output adapter."""

from datetime import date
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from weather_map.adapters.output.open_meteo.client import OpenMeteoHistoricalWeatherClient
from weather_map.application.dtos import WeatherMapSettings
from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.exceptions import WeatherDataUnavailableError
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


def test_open_meteo_client_batches_locations_into_single_request() -> None:
    """The adapter should send multiple locations as comma-separated coordinates."""

    def handler(request: httpx.Request) -> httpx.Response:
        query = parse_qs(urlparse(str(request.url)).query)
        assert query["latitude"] == ["50.0,51.0"]
        assert query["longitude"] == ["14.0,15.0"]
        return httpx.Response(
            status_code=200,
            json=[
                {
                    "hourly": {
                        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                        "temperature_2m": [1.0, 2.5],
                    }
                },
                {
                    "hourly": {
                        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                        "temperature_2m": [3.0, 4.5],
                    }
                },
            ],
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    adapter = OpenMeteoHistoricalWeatherClient(WeatherMapSettings(), client=client)

    result = adapter.fetch(
        HistoricalWeatherSampleRequest(
            locations=(
                GeoPoint(latitude=50.0, longitude=14.0),
                GeoPoint(latitude=51.0, longitude=15.0),
            ),
            layer=WeatherLayer.TEMPERATURE,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
        )
    )

    assert [series.location for series in result] == [
        GeoPoint(latitude=50.0, longitude=14.0),
        GeoPoint(latitude=51.0, longitude=15.0),
    ]
    assert [series.values for series in result] == [(1.0, 2.5), (3.0, 4.5)]


def test_open_meteo_client_raises_for_mismatched_location_count() -> None:
    """The adapter should fail when the multi-location response count is inconsistent."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json=[
                {
                    "hourly": {
                        "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                        "temperature_2m": [1.0, 2.5],
                    }
                }
            ],
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    adapter = OpenMeteoHistoricalWeatherClient(WeatherMapSettings(), client=client)

    with pytest.raises(WeatherDataUnavailableError, match="location count"):
        adapter.fetch(
            HistoricalWeatherSampleRequest(
                locations=(
                    GeoPoint(latitude=50.0, longitude=14.0),
                    GeoPoint(latitude=51.0, longitude=15.0),
                ),
                layer=WeatherLayer.TEMPERATURE,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 1),
            )
        )
