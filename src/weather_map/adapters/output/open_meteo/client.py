"""Open-Meteo adapter for historical archive retrieval."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, date, datetime

import httpx

from weather_map.adapters.output.open_meteo.dtos import (
    OpenMeteoArchiveLocationData,
    OpenMeteoArchiveRequest,
    OpenMeteoDailyData,
    OpenMeteoDailyVariable,
    OpenMeteoHourlyData,
    OpenMeteoHourlyVariable,
)
from weather_map.adapters.output.open_meteo.settings import OpenMeteoClientSettings
from weather_map.domain.exceptions import WeatherDataUnavailableError
from weather_map.domain.geo import GeoPoint


class OpenMeteoHistoricalWeatherClient:
    """Retrieve raw historical weather series from the Open-Meteo archive API."""

    def __init__(self, settings: OpenMeteoClientSettings, client: httpx.Client | None = None) -> None:
        """Initialize the adapter with runtime settings."""
        self._settings = settings
        self._client = client or httpx.Client(timeout=settings.request_timeout_seconds)

    def fetch_archive(self, request: OpenMeteoArchiveRequest) -> list[OpenMeteoArchiveLocationData]:
        """Fetch raw Open-Meteo hourly and daily series for each requested location."""
        params: dict[str, str] = {
            "latitude": ",".join(str(location.latitude) for location in request.locations),
            "longitude": ",".join(str(location.longitude) for location in request.locations),
            "start_date": request.start_date.isoformat(),
            "end_date": request.end_date.isoformat(),
            "timezone": "UTC",
        }
        if request.hourly_variables:
            params["hourly"] = ",".join(variable.value for variable in request.hourly_variables)
        if request.daily_variables:
            params["daily"] = ",".join(variable.value for variable in request.daily_variables)
        try:
            response = self._client.get(self._settings.base_url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as error:
            msg = "Unable to retrieve historical weather data from Open-Meteo"
            raise WeatherDataUnavailableError(msg) from error

        payload = response.json()
        response_payloads = self._coerce_payloads(payload)
        if len(response_payloads) != len(request.locations):
            msg = "Open-Meteo response location count does not match request"
            raise WeatherDataUnavailableError(msg)

        results: list[OpenMeteoArchiveLocationData] = []
        for location, response_payload in zip(request.locations, response_payloads, strict=True):
            results.append(
                self._parse_response(
                    location=location,
                    payload=response_payload,
                    hourly_variables=request.hourly_variables,
                    daily_variables=request.daily_variables,
                )
            )
        return results

    def _coerce_payloads(self, payload: object) -> list[dict[str, object]]:
        """Normalize single-location and multi-location API responses into a list."""
        if isinstance(payload, dict):
            return [payload]
        if isinstance(payload, Sequence) and not isinstance(payload, str):
            payloads = [item for item in payload if isinstance(item, dict)]
            if len(payloads) != len(payload):
                msg = "Open-Meteo multi-location response contains invalid items"
                raise WeatherDataUnavailableError(msg)
            return payloads
        msg = "Open-Meteo response has an unsupported shape"
        raise WeatherDataUnavailableError(msg)

    def _parse_response(
        self,
        location: GeoPoint,
        payload: dict[str, object],
        hourly_variables: tuple[OpenMeteoHourlyVariable, ...],
        daily_variables: tuple[OpenMeteoDailyVariable, ...],
    ) -> OpenMeteoArchiveLocationData:
        """Convert an Open-Meteo response payload into a stable archive DTO."""
        hourly_timestamps_utc, hourly_values_by_variable = self._parse_hourly_section(payload, hourly_variables)
        daily_dates, daily_values_by_variable = self._parse_daily_section(payload, daily_variables)

        hourly = (
            OpenMeteoHourlyData(
                timestamps_utc=hourly_timestamps_utc,
                values_by_variable=hourly_values_by_variable,
            )
            if hourly_values_by_variable
            else None
        )
        daily = (
            OpenMeteoDailyData(
                dates=daily_dates,
                values_by_variable=daily_values_by_variable,
            )
            if daily_values_by_variable
            else None
        )

        return OpenMeteoArchiveLocationData(
            location=location,
            hourly=hourly,
            daily=daily,
        )

    def _parse_hourly_section(
        self,
        payload: dict[str, object],
        hourly_variables: tuple[OpenMeteoHourlyVariable, ...],
    ) -> tuple[tuple[datetime, ...], dict[OpenMeteoHourlyVariable, tuple[float, ...]]]:
        """Parse hourly timestamps and values for the requested variables."""
        if not hourly_variables:
            return (), {}

        hourly = payload.get("hourly")
        if not isinstance(hourly, dict):
            msg = "Open-Meteo response is missing hourly data"
            raise WeatherDataUnavailableError(msg)
        raw_timestamps = hourly.get("time")
        if not isinstance(raw_timestamps, list):
            msg = "Open-Meteo response is missing hourly timestamps"
            raise WeatherDataUnavailableError(msg)

        hourly_timestamps_utc = tuple(
            datetime.fromisoformat(f"{raw_timestamp}:00+00:00").astimezone(UTC)
            for raw_timestamp in raw_timestamps
            if isinstance(raw_timestamp, str)
        )
        hourly_values_by_variable: dict[OpenMeteoHourlyVariable, tuple[float, ...]] = {}
        for variable in hourly_variables:
            raw_values = hourly.get(variable.value)
            if not isinstance(raw_values, list):
                msg = f"Open-Meteo response is missing hourly series values for {variable.value}"
                raise WeatherDataUnavailableError(msg)
            values = tuple(float(raw_value) for raw_value in raw_values if isinstance(raw_value, int | float))
            if len(hourly_timestamps_utc) != len(values):
                msg = "Open-Meteo response contains mismatched hourly timestamp/value lengths"
                raise WeatherDataUnavailableError(msg)
            hourly_values_by_variable[variable] = values
        return hourly_timestamps_utc, hourly_values_by_variable

    def _parse_daily_section(
        self,
        payload: dict[str, object],
        daily_variables: tuple[OpenMeteoDailyVariable, ...],
    ) -> tuple[tuple[date, ...], dict[OpenMeteoDailyVariable, tuple[float | date | datetime | str, ...]]]:
        """Parse daily dates and values for the requested variables."""
        if not daily_variables:
            return (), {}

        daily = payload.get("daily")
        if not isinstance(daily, dict):
            msg = "Open-Meteo response is missing daily data"
            raise WeatherDataUnavailableError(msg)
        raw_dates = daily.get("time")
        if not isinstance(raw_dates, list):
            msg = "Open-Meteo response is missing daily dates"
            raise WeatherDataUnavailableError(msg)

        daily_dates = tuple(date.fromisoformat(raw_date) for raw_date in raw_dates if isinstance(raw_date, str))
        daily_values_by_variable: dict[OpenMeteoDailyVariable, tuple[float | date | datetime | str, ...]] = {}
        for variable in daily_variables:
            raw_values = daily.get(variable.value)
            if not isinstance(raw_values, list):
                msg = f"Open-Meteo response is missing daily series values for {variable.value}"
                raise WeatherDataUnavailableError(msg)
            values = tuple(self._coerce_daily_value(raw_value) for raw_value in raw_values)
            if len(daily_dates) != len(values):
                msg = "Open-Meteo response contains mismatched daily date/value lengths"
                raise WeatherDataUnavailableError(msg)
            daily_values_by_variable[variable] = values
        return daily_dates, daily_values_by_variable

    def _coerce_daily_value(self, raw_value: object) -> float | date | datetime | str:
        """Normalize daily payload values into stable Python primitives."""
        if isinstance(raw_value, int | float):
            return float(raw_value)
        if isinstance(raw_value, str):
            try:
                return datetime.fromisoformat(raw_value)
            except ValueError:
                try:
                    return date.fromisoformat(raw_value)
                except ValueError:
                    return raw_value
        msg = "Open-Meteo daily response contains an unsupported value type"
        raise WeatherDataUnavailableError(msg)
