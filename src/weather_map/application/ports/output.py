"""Output ports for infrastructure dependencies."""

from __future__ import annotations

from typing import Protocol

from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.weather import LocationWeatherSeries


class HistoricalWeatherProviderPort(Protocol):
    """Port for retrieving historical weather data from an external source."""

    def fetch(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        """Retrieve weather time series for the requested locations."""
        ...


class HistoricalWeatherCachePort(Protocol):
    """Port for caching weather time series results."""

    def get(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries] | None:
        """Return cached weather series when available."""
        ...

    def set(self, request: HistoricalWeatherSampleRequest, series: list[LocationWeatherSeries]) -> None:
        """Store weather series for later reuse."""
        ...
