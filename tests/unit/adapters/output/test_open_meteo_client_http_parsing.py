"""HTTP-shape and parsing tests for the Open-Meteo output adapter."""

from datetime import date

import httpx

from weather_map.adapters.output.open_meteo import (
    OpenMeteoArchiveRequest,
    OpenMeteoClientSettings,
    OpenMeteoDailyVariable,
    OpenMeteoHistoricalWeatherClient,
    OpenMeteoHourlyVariable,
)
from weather_map.domain.geo import GeoPoint


def test_open_meteo_client_parses_combined_hourly_and_daily_archive_response() -> None:
    """The adapter should parse a mixed hourly/daily archive payload end to end."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get("hourly") == "temperature_2m,wind_speed_10m"
        assert request.url.params.get("daily") == "temperature_2m_max"
        return httpx.Response(
            status_code=200,
            json={
                "hourly": {
                    "time": ["2024-01-01T00:00", "2024-01-01T01:00"],
                    "temperature_2m": [1.0, 2.5],
                    "wind_speed_10m": [5.0, 7.0],
                },
                "daily": {
                    "time": ["2024-01-01"],
                    "temperature_2m_max": [6.0],
                },
            },
        )

    adapter = OpenMeteoHistoricalWeatherClient(
        OpenMeteoClientSettings(base_url="https://archive-api.open-meteo.com/v1/archive", request_timeout_seconds=15.0),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    result = adapter.fetch_archive(
        OpenMeteoArchiveRequest(
            locations=(GeoPoint(latitude=50.0, longitude=14.0),),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            hourly_variables=(
                OpenMeteoHourlyVariable.TEMPERATURE_2M,
                OpenMeteoHourlyVariable.WIND_SPEED_10M,
            ),
            daily_variables=(OpenMeteoDailyVariable.TEMPERATURE_2M_MAX,),
        )
    )

    assert len(result) == 1
    assert result[0].hourly is not None
    assert result[0].hourly.values_by_variable[OpenMeteoHourlyVariable.WIND_SPEED_10M] == (5.0, 7.0)
    assert result[0].daily is not None
    assert result[0].daily.values_by_variable[OpenMeteoDailyVariable.TEMPERATURE_2M_MAX] == (6.0,)
