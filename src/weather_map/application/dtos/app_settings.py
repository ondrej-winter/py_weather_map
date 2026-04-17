"""Application-facing runtime settings DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_OPENMETEO_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"
DEFAULT_LOCAL_WEATHER_DATA_DIRECTORY = Path("data/weather_history")


@dataclass(frozen=True, slots=True)
class WeatherMapSettings:
    """Canonical runtime settings used by the application."""

    openmeteo_base_url: str = DEFAULT_OPENMETEO_BASE_URL
    request_timeout_seconds: float = 15.0
    local_weather_data_directory: Path = field(default_factory=lambda: DEFAULT_LOCAL_WEATHER_DATA_DIRECTORY)
    local_weather_coordinate_precision: int = 4
    host: str = "127.0.0.1"
    port: int = 8000
    default_grid_rows: int = 8
    default_grid_columns: int = 8
    max_grid_rows: int = 20
    max_grid_columns: int = 20

    def __post_init__(self) -> None:
        """Validate application-visible settings invariants."""
        if not self.openmeteo_base_url.strip():
            msg = "openmeteo_base_url must not be blank"
            raise ValueError(msg)
        if self.request_timeout_seconds <= 0:
            msg = "request_timeout_seconds must be positive"
            raise ValueError(msg)
        if self.local_weather_coordinate_precision < 0:
            msg = "local_weather_coordinate_precision must be non-negative"
            raise ValueError(msg)
        if not self.host.strip():
            msg = "host must not be blank"
            raise ValueError(msg)
        if not 1 <= self.port <= 65535:
            msg = "port must be between 1 and 65535"
            raise ValueError(msg)
        if self.default_grid_rows < 2 or self.default_grid_columns < 2:
            msg = "default grid dimensions must be at least 2"
            raise ValueError(msg)
        if self.max_grid_rows < self.default_grid_rows or self.max_grid_columns < self.default_grid_columns:
            msg = "max grid dimensions must be greater than or equal to defaults"
            raise ValueError(msg)
