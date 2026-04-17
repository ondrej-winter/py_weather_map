"""Open-Meteo-specific request and response DTOs owned by the adapter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum

from weather_map.domain.exceptions import InvalidHeatmapQueryError
from weather_map.domain.geo import GeoPoint


class OpenMeteoHourlyVariable(StrEnum):
    """Supported hourly variables for the Open-Meteo archive API."""

    TEMPERATURE_2M = "temperature_2m"
    PRECIPITATION = "precipitation"
    RELATIVE_HUMIDITY_2M = "relative_humidity_2m"
    WIND_SPEED_10M = "wind_speed_10m"


class OpenMeteoDailyVariable(StrEnum):
    """Supported daily variables for the Open-Meteo archive API."""

    WEATHER_CODE = "weather_code"
    TEMPERATURE_2M_MAX = "temperature_2m_max"
    TEMPERATURE_2M_MIN = "temperature_2m_min"
    TEMPERATURE_2M_MEAN = "temperature_2m_mean"
    APPARENT_TEMPERATURE_MAX = "apparent_temperature_max"
    APPARENT_TEMPERATURE_MIN = "apparent_temperature_min"
    APPARENT_TEMPERATURE_MEAN = "apparent_temperature_mean"
    SUNRISE = "sunrise"
    SUNSET = "sunset"
    DAYLIGHT_DURATION = "daylight_duration"
    SUNSHINE_DURATION = "sunshine_duration"
    PRECIPITATION_SUM = "precipitation_sum"
    RAIN_SUM = "rain_sum"
    SNOWFALL_SUM = "snowfall_sum"
    PRECIPITATION_HOURS = "precipitation_hours"
    WIND_SPEED_10M_MAX = "wind_speed_10m_max"
    WIND_GUSTS_10M_MAX = "wind_gusts_10m_max"
    SHORTWAVE_RADIATION_SUM = "shortwave_radiation_sum"
    ET0_FAO_EVAPOTRANSPIRATION = "et0_fao_evapotranspiration"


@dataclass(frozen=True)
class OpenMeteoArchiveRequest:
    """Request DTO for the Open-Meteo historical archive API."""

    locations: tuple[GeoPoint, ...]
    start_date: date
    end_date: date
    hourly_variables: tuple[OpenMeteoHourlyVariable, ...] = ()
    daily_variables: tuple[OpenMeteoDailyVariable, ...] = ()

    def __post_init__(self) -> None:
        """Validate request invariants."""
        if not self.locations:
            msg = "locations must not be empty"
            raise InvalidHeatmapQueryError(msg)
        if self.end_date < self.start_date:
            msg = "end_date must be greater than or equal to start_date"
            raise InvalidHeatmapQueryError(msg)
        if not self.hourly_variables and not self.daily_variables:
            msg = "at least one hourly or daily variable must be requested"
            raise InvalidHeatmapQueryError(msg)


@dataclass(frozen=True)
class OpenMeteoHourlyData:
    """Hourly archive payload for one location."""

    timestamps_utc: tuple[datetime, ...]
    values_by_variable: dict[OpenMeteoHourlyVariable, tuple[float, ...]]

    def __post_init__(self) -> None:
        """Validate timestamp/value alignment and timezone normalization."""
        for timestamp in self.timestamps_utc:
            if timestamp.tzinfo is None or timestamp.utcoffset() != UTC.utcoffset(timestamp):
                msg = "timestamps must be timezone-aware UTC datetimes"
                raise InvalidHeatmapQueryError(msg)
        for hourly_values in self.values_by_variable.values():
            if len(self.timestamps_utc) != len(hourly_values):
                msg = "hourly timestamps and values must have equal length"
                raise InvalidHeatmapQueryError(msg)


@dataclass(frozen=True)
class OpenMeteoDailyData:
    """Daily archive payload for one location."""

    dates: tuple[date, ...]
    values_by_variable: dict[OpenMeteoDailyVariable, tuple[float | date | datetime | str, ...]]

    def __post_init__(self) -> None:
        """Validate daily date/value alignment."""
        for daily_values in self.values_by_variable.values():
            if len(self.dates) != len(daily_values):
                msg = "daily dates and values must have equal length"
                raise InvalidHeatmapQueryError(msg)


@dataclass(frozen=True)
class OpenMeteoArchiveLocationData:
    """Complete Open-Meteo archive payload for one location."""

    location: GeoPoint
    hourly: OpenMeteoHourlyData | None = None
    daily: OpenMeteoDailyData | None = None

    def __post_init__(self) -> None:
        """Require at least one populated archive section."""
        if self.hourly is None and self.daily is None:
            msg = "at least one archive section must be present"
            raise InvalidHeatmapQueryError(msg)
