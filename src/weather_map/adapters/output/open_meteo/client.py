"""Open-Meteo adapter for historical weather retrieval."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx

from weather_map.domain.exceptions import WeatherDataUnavailableError
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import LocationWeatherSeries, get_layer_definition

if TYPE_CHECKING:
    from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
    from weather_map.config import WeatherMapSettings


class OpenMeteoHistoricalWeatherClient:
    """Retrieve historical weather series from the Open-Meteo archive API."""

    def __init__(self, settings: WeatherMapSettings, client: httpx.Client | None = None) -> None:
        """Initialize the adapter with runtime settings."""
        self._settings = settings
        self._client = client or httpx.Client(timeout=settings.request_timeout_seconds)

    def fetch(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        """Fetch weather series for each requested location."""
        layer_definition = get_layer_definition(request.layer)
        results: list[LocationWeatherSeries] = []
        for location in request.locations:
            params: dict[str, str | float] = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "start_date": request.start_date.isoformat(),
                "end_date": request.end_date.isoformat(),
                "hourly": layer_definition.openmeteo_hourly_variable,
                "timezone": "UTC",
            }
            try:
                response = self._client.get(self._settings.openmeteo_base_url, params=params)
                response.raise_for_status()
            except httpx.HTTPError as error:
                msg = "Unable to retrieve historical weather data from Open-Meteo"
                raise WeatherDataUnavailableError(msg) from error
            results.append(
                self._parse_response(
                    location.latitude,
                    location.longitude,
                    response.json(),
                    layer_definition.openmeteo_hourly_variable,
                )
            )
        return results

    def _parse_response(
        self,
        latitude: float,
        longitude: float,
        payload: dict[str, object],
        hourly_variable: str,
    ) -> LocationWeatherSeries:
        """Convert an Open-Meteo response payload into a domain time series."""
        hourly = payload.get("hourly")
        if not isinstance(hourly, dict):
            msg = "Open-Meteo response is missing hourly data"
            raise WeatherDataUnavailableError(msg)
        raw_timestamps = hourly.get("time")
        raw_values = hourly.get(hourly_variable)
        if not isinstance(raw_timestamps, list) or not isinstance(raw_values, list):
            msg = "Open-Meteo response is missing hourly series values"
            raise WeatherDataUnavailableError(msg)
        timestamps = tuple(
            datetime.fromisoformat(f"{raw_timestamp}:00+00:00").astimezone(UTC)
            for raw_timestamp in raw_timestamps
            if isinstance(raw_timestamp, str)
        )
        values = tuple(float(raw_value) for raw_value in raw_values if isinstance(raw_value, int | float))
        if len(timestamps) != len(values):
            msg = "Open-Meteo response contains mismatched timestamp/value lengths"
            raise WeatherDataUnavailableError(msg)
        return LocationWeatherSeries(
            location=GeoPoint(latitude=latitude, longitude=longitude),
            timestamps_utc=timestamps,
            values=values,
        )
