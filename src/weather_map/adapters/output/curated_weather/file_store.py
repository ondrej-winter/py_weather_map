"""File-backed curated weather store for offline-first historical lookups."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from weather_map.application.dtos.weather_heatmap import HistoricalWeatherSampleRequest
from weather_map.domain.geo import GeoPoint
from weather_map.domain.weather import LocationWeatherSeries


class FileBackedCuratedHistoricalWeatherStore:
    """Persist historical weather series as deterministic JSON files."""

    def __init__(self, root_directory: Path, coordinate_precision: int = 4) -> None:
        """Initialize the curated store settings."""
        self._root_directory = root_directory
        self._coordinate_precision = coordinate_precision

    def fetch_available(self, request: HistoricalWeatherSampleRequest) -> list[LocationWeatherSeries]:
        """Return all series already present in local curated storage."""
        available_series: list[LocationWeatherSeries] = []
        for location in request.locations:
            path = self._build_path(request=request, location=location)
            if not path.exists():
                continue
            available_series.append(self._load_series(path))
        return available_series

    def save(self, request: HistoricalWeatherSampleRequest, series: list[LocationWeatherSeries]) -> None:
        """Store provided series in curated JSON files."""
        for location_series in series:
            path = self._build_path(request=request, location=location_series.location)
            path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "location": {
                    "latitude": location_series.location.latitude,
                    "longitude": location_series.location.longitude,
                },
                "timestamps_utc": [timestamp.isoformat() for timestamp in location_series.timestamps_utc],
                "values": list(location_series.values),
            }
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _build_path(self, request: HistoricalWeatherSampleRequest, location: GeoPoint) -> Path:
        """Build the deterministic JSON path for one series."""
        rounded_latitude = self._format_coordinate(location.latitude)
        rounded_longitude = self._format_coordinate(location.longitude)
        return (
            self._root_directory
            / request.layer.value
            / request.start_date.isoformat()
            / request.end_date.isoformat()
            / f"{rounded_latitude}_{rounded_longitude}.json"
        )

    def _format_coordinate(self, coordinate: float) -> str:
        """Format a coordinate for stable filenames."""
        rounded_coordinate = round(coordinate, self._coordinate_precision)
        return f"{rounded_coordinate:.{self._coordinate_precision}f}".replace("-", "m").replace(".", "p")

    def _load_series(self, path: Path) -> LocationWeatherSeries:
        """Load one curated series file into a domain object."""
        payload = json.loads(path.read_text(encoding="utf-8"))
        location_payload = payload["location"]
        return LocationWeatherSeries(
            location=GeoPoint(
                latitude=float(location_payload["latitude"]),
                longitude=float(location_payload["longitude"]),
            ),
            timestamps_utc=tuple(datetime.fromisoformat(timestamp) for timestamp in payload["timestamps_utc"]),
            values=tuple(float(value) for value in payload["values"]),
        )
