"""Input ports for weather-map use cases."""

from __future__ import annotations

from typing import Protocol

from weather_map.application.dtos.weather_heatmap import HeatmapQuery, HeatmapResponse, LayerOptionDTO


class WeatherHeatmapQueryPort(Protocol):
    """Port for retrieving heatmap data for a viewport."""

    def execute(self, query: HeatmapQuery) -> HeatmapResponse:
        """Execute the heatmap query."""
        ...


class AvailableWeatherLayersPort(Protocol):
    """Port for listing supported weather layers."""

    def execute(self) -> list[LayerOptionDTO]:
        """Return supported layer metadata."""
        ...
