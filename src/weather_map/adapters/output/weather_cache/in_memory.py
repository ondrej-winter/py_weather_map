"""In-memory cache adapter for historical weather data."""

from __future__ import annotations

from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.weather import LocationWeatherSeries


class InMemoryHistoricalWeatherCache:
    """Cache weather series keyed by request parameters."""

    def __init__(self) -> None:
        """Initialize an empty in-memory cache."""
        self._storage: dict[str, list[LocationWeatherSeries]] = {}

    def get(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries] | None:
        """Return cached series for a request, if present."""
        return self._storage.get(self._build_key(request))

    def set(self, request: HistoricalWeatherSampleRequest, series: list[LocationWeatherSeries]) -> None:
        """Store series for the given request."""
        self._storage[self._build_key(request)] = list(series)

    def _build_key(self, request: HistoricalWeatherSampleRequest) -> str:
        """Build a deterministic cache key for the request."""
        locations = ";".join(f"{location.latitude:.4f},{location.longitude:.4f}" for location in request.locations)
        return f"{request.layer}|{request.start_date.isoformat()}|{request.end_date.isoformat()}|{locations}"
