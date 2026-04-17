"""Live integration test for the Open-Meteo output adapter."""

from __future__ import annotations

import os
from datetime import date

import pytest

from weather_map.adapters.output.open_meteo import (
    OpenMeteoArchiveRequest,
    OpenMeteoClientSettings,
    OpenMeteoDailyVariable,
    OpenMeteoHistoricalWeatherClient,
    OpenMeteoHourlyVariable,
)
from weather_map.domain.geo import GeoPoint

pytestmark = [
    pytest.mark.live_external,
    pytest.mark.skipif(
        os.getenv("WEATHER_MAP_RUN_LIVE_TESTS") != "1",
        reason="Set WEATHER_MAP_RUN_LIVE_TESTS=1 to enable live external integration tests.",
    ),
]


def test_open_meteo_client_fetches_live_combined_hourly_and_daily_archive_response() -> None:
    """The adapter should fetch and parse a real Open-Meteo archive response."""
    adapter = OpenMeteoHistoricalWeatherClient(
        OpenMeteoClientSettings(
            base_url="https://archive-api.open-meteo.com/v1/archive",
            request_timeout_seconds=15.0,
        )
    )

    result = adapter.fetch_archive(
        OpenMeteoArchiveRequest(
            locations=(GeoPoint(latitude=50.0755, longitude=14.4378),),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 2),
            hourly_variables=(OpenMeteoHourlyVariable.TEMPERATURE_2M,),
            daily_variables=(OpenMeteoDailyVariable.TEMPERATURE_2M_MAX,),
        )
    )

    assert len(result) == 1
    assert result[0].location == GeoPoint(latitude=50.0755, longitude=14.4378)

    assert result[0].hourly is not None
    assert OpenMeteoHourlyVariable.TEMPERATURE_2M in result[0].hourly.values_by_variable
    assert len(result[0].hourly.timestamps_utc) > 0
    assert len(result[0].hourly.values_by_variable[OpenMeteoHourlyVariable.TEMPERATURE_2M]) == len(
        result[0].hourly.timestamps_utc
    )

    assert result[0].daily is not None
    assert OpenMeteoDailyVariable.TEMPERATURE_2M_MAX in result[0].daily.values_by_variable
    assert len(result[0].daily.dates) > 0
    assert len(result[0].daily.values_by_variable[OpenMeteoDailyVariable.TEMPERATURE_2M_MAX]) == len(
        result[0].daily.dates
    )
