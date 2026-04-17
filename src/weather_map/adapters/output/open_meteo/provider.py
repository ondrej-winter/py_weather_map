"""Application-facing historical weather provider backed by Open-Meteo."""

from __future__ import annotations

from typing import Protocol

from weather_map.adapters.output.open_meteo.dtos import (
    OpenMeteoArchiveLocationData,
    OpenMeteoArchiveRequest,
    OpenMeteoHourlyVariable,
)
from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.weather import LocationWeatherSeries, get_layer_definition


class OpenMeteoArchiveClientProtocol(Protocol):
    """Protocol for raw Open-Meteo archive fetch clients."""

    def fetch_archive(self, request: OpenMeteoArchiveRequest) -> list[OpenMeteoArchiveLocationData]:
        """Fetch raw hourly archive series from Open-Meteo."""
        ...


class OpenMeteoHistoricalWeatherProvider:
    """Translate weather sampling requests into Open-Meteo archive fetches."""

    def __init__(self, client: OpenMeteoArchiveClientProtocol) -> None:
        """Initialize the provider with the raw Open-Meteo client."""
        self._client = client

    def fetch(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        """Fetch normalized weather series for the requested layer and locations."""
        layer_definition = get_layer_definition(request.layer)
        archive_request = OpenMeteoArchiveRequest(
            locations=request.locations,
            start_date=request.start_date,
            end_date=request.end_date,
            hourly_variables=(OpenMeteoHourlyVariable(layer_definition.openmeteo_hourly_variable),),
        )
        archive_series = self._client.fetch_archive(archive_request)
        requested_variable = OpenMeteoHourlyVariable(layer_definition.openmeteo_hourly_variable)
        return [
            LocationWeatherSeries(
                location=series.location,
                timestamps_utc=series.hourly.timestamps_utc if series.hourly is not None else (),
                values=series.hourly.values_by_variable[requested_variable] if series.hourly is not None else (),
            )
            for series in archive_series
        ]
