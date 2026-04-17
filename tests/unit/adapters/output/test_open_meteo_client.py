"""Tests for the Open-Meteo output adapter."""

from datetime import date
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from weather_map.adapters.output.open_meteo import (
    OpenMeteoArchiveRequest,
    OpenMeteoClientSettings,
    OpenMeteoDailyVariable,
    OpenMeteoHistoricalWeatherClient,
    OpenMeteoHourlyVariable,
)
from weather_map.domain.exceptions import WeatherDataUnavailableError
from weather_map.domain.geo import GeoPoint


def test_open_meteo_client_parses_hourly_response() -> None:
    """The adapter should parse Open-Meteo hourly series into archive DTOs."""

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
    adapter = OpenMeteoHistoricalWeatherClient(
        OpenMeteoClientSettings(base_url="https://archive-api.open-meteo.com/v1/archive", request_timeout_seconds=15.0),
        client=client,
    )

    result = adapter.fetch_archive(
        OpenMeteoArchiveRequest(
            locations=(GeoPoint(latitude=50.0, longitude=14.0),),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            hourly_variables=(OpenMeteoHourlyVariable.TEMPERATURE_2M,),
        )
    )

    assert result[0].hourly is not None
    assert result[0].hourly.values_by_variable == {OpenMeteoHourlyVariable.TEMPERATURE_2M: (1.0, 2.5)}
    assert result[0].location == GeoPoint(latitude=50.0, longitude=14.0)


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
    adapter = OpenMeteoHistoricalWeatherClient(
        OpenMeteoClientSettings(base_url="https://archive-api.open-meteo.com/v1/archive", request_timeout_seconds=15.0),
        client=client,
    )

    result = adapter.fetch_archive(
        OpenMeteoArchiveRequest(
            locations=(
                GeoPoint(latitude=50.0, longitude=14.0),
                GeoPoint(latitude=51.0, longitude=15.0),
            ),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            hourly_variables=(OpenMeteoHourlyVariable.TEMPERATURE_2M,),
        )
    )

    assert [series.location for series in result] == [
        GeoPoint(latitude=50.0, longitude=14.0),
        GeoPoint(latitude=51.0, longitude=15.0),
    ]
    assert [series.hourly.values_by_variable if series.hourly is not None else None for series in result] == [
        {OpenMeteoHourlyVariable.TEMPERATURE_2M: (1.0, 2.5)},
        {OpenMeteoHourlyVariable.TEMPERATURE_2M: (3.0, 4.5)},
    ]


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
    adapter = OpenMeteoHistoricalWeatherClient(
        OpenMeteoClientSettings(base_url="https://archive-api.open-meteo.com/v1/archive", request_timeout_seconds=15.0),
        client=client,
    )

    with pytest.raises(WeatherDataUnavailableError, match="location count"):
        adapter.fetch_archive(
            OpenMeteoArchiveRequest(
                locations=(
                    GeoPoint(latitude=50.0, longitude=14.0),
                    GeoPoint(latitude=51.0, longitude=15.0),
                ),
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 1),
                hourly_variables=(OpenMeteoHourlyVariable.TEMPERATURE_2M,),
            )
        )


def test_open_meteo_client_supports_multiple_hourly_and_daily_variables() -> None:
    """The adapter should parse multiple hourly and daily variable series in one response."""

    def handler(request: httpx.Request) -> httpx.Response:
        query = parse_qs(urlparse(str(request.url)).query)
        assert query["hourly"] == ["temperature_2m,relative_humidity_2m"]
        assert query["daily"] == ["temperature_2m_max,weather_code"]
        return httpx.Response(
            status_code=200,
            json={
                "hourly": {
                    "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                    "temperature_2m": [1.0, 2.5],
                    "relative_humidity_2m": [80, 82],
                },
                "daily": {
                    "time": ["2024-01-01", "2024-01-02"],
                    "temperature_2m_max": [4.5, 5.0],
                    "weather_code": [3, 61],
                },
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    adapter = OpenMeteoHistoricalWeatherClient(
        OpenMeteoClientSettings(base_url="https://archive-api.open-meteo.com/v1/archive", request_timeout_seconds=15.0),
        client=client,
    )

    result = adapter.fetch_archive(
        OpenMeteoArchiveRequest(
            locations=(GeoPoint(latitude=50.0, longitude=14.0),),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            hourly_variables=(
                OpenMeteoHourlyVariable.TEMPERATURE_2M,
                OpenMeteoHourlyVariable.RELATIVE_HUMIDITY_2M,
            ),
            daily_variables=(
                OpenMeteoDailyVariable.TEMPERATURE_2M_MAX,
                OpenMeteoDailyVariable.WEATHER_CODE,
            ),
        )
    )

    assert result[0].hourly is not None
    assert result[0].hourly.values_by_variable == {
        OpenMeteoHourlyVariable.TEMPERATURE_2M: (1.0, 2.5),
        OpenMeteoHourlyVariable.RELATIVE_HUMIDITY_2M: (80.0, 82.0),
    }
    assert result[0].daily is not None
    assert result[0].daily.values_by_variable == {
        OpenMeteoDailyVariable.TEMPERATURE_2M_MAX: (4.5, 5.0),
        OpenMeteoDailyVariable.WEATHER_CODE: (3.0, 61.0),
    }
