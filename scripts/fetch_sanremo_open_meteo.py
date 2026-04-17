"""Fetch all supported Open-Meteo archive variables for central Sanremo."""

from __future__ import annotations

import json
from datetime import date, datetime

from weather_map.adapters.output.open_meteo import (
    OpenMeteoArchiveRequest,
    OpenMeteoClientSettings,
    OpenMeteoDailyData,
    OpenMeteoDailyVariable,
    OpenMeteoHistoricalWeatherClient,
    OpenMeteoHourlyData,
    OpenMeteoHourlyVariable,
)
from weather_map.domain.geo import GeoPoint

SANREMO_CENTER = GeoPoint(latitude=43.8170, longitude=7.7770)
START_DATE = date(2025, 1, 1)
END_DATE = date(2025, 1, 2)


def _serialize_hourly(hourly: OpenMeteoHourlyData | None) -> dict[str, object] | None:
    """Convert hourly data into a JSON-serializable structure."""
    if hourly is None:
        return None
    return {
        "timestamps_utc": [timestamp.isoformat() for timestamp in hourly.timestamps_utc],
        "values_by_variable": {variable.value: list(values) for variable, values in hourly.values_by_variable.items()},
    }


def _serialize_daily(daily: OpenMeteoDailyData | None) -> dict[str, object] | None:
    """Convert daily data into a JSON-serializable structure."""
    if daily is None:
        return None
    return {
        "dates": [value.isoformat() for value in daily.dates],
        "values_by_variable": {
            variable.value: [_serialize_daily_value(value) for value in values]
            for variable, values in daily.values_by_variable.items()
        },
    }


def _serialize_daily_value(value: float | date | datetime | str) -> float | str:
    """Convert a supported daily value into JSON-friendly output."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def main() -> None:
    """Fetch and print all supported Open-Meteo archive data for Sanremo center."""
    client = OpenMeteoHistoricalWeatherClient(
        OpenMeteoClientSettings(
            base_url="https://archive-api.open-meteo.com/v1/archive",
            request_timeout_seconds=30.0,
        )
    )
    request = OpenMeteoArchiveRequest(
        locations=(SANREMO_CENTER,),
        start_date=START_DATE,
        end_date=END_DATE,
        hourly_variables=tuple(OpenMeteoHourlyVariable),
        daily_variables=tuple(OpenMeteoDailyVariable),
    )

    response = client.fetch_archive(request)
    serialized = [
        {
            "location": {
                "latitude": item.location.latitude,
                "longitude": item.location.longitude,
            },
            "hourly": _serialize_hourly(item.hourly),
            "daily": _serialize_daily(item.daily),
        }
        for item in response
    ]
    print(json.dumps(serialized, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
