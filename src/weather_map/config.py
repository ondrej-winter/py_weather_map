"""Runtime configuration for the weather map application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WeatherMapSettings:
    """Application settings loaded from environment variables."""

    openmeteo_base_url: str = "https://archive-api.open-meteo.com/v1/archive"
    request_timeout_seconds: float = 15.0
    local_weather_data_directory: Path = Path("data/weather_history")
    local_weather_coordinate_precision: int = 4
    host: str = "127.0.0.1"
    port: int = 8000
    default_grid_rows: int = 8
    default_grid_columns: int = 8
    max_grid_rows: int = 20
    max_grid_columns: int = 20

    def __post_init__(self) -> None:
        """Validate settings values."""
        if self.request_timeout_seconds <= 0:
            msg = "request_timeout_seconds must be positive"
            raise ValueError(msg)
        if self.local_weather_coordinate_precision < 0:
            msg = "local_weather_coordinate_precision must be non-negative"
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


def load_settings() -> WeatherMapSettings:
    """Load application settings from environment variables."""
    return WeatherMapSettings(
        openmeteo_base_url=os.getenv("WEATHER_MAP_OPENMETEO_BASE_URL", "https://archive-api.open-meteo.com/v1/archive"),
        request_timeout_seconds=float(os.getenv("WEATHER_MAP_REQUEST_TIMEOUT_SECONDS", "15.0")),
        local_weather_data_directory=Path(
            os.getenv("WEATHER_MAP_LOCAL_WEATHER_DATA_DIRECTORY", "data/weather_history")
        ),
        local_weather_coordinate_precision=int(os.getenv("WEATHER_MAP_LOCAL_WEATHER_COORDINATE_PRECISION", "4")),
        host=os.getenv("WEATHER_MAP_HOST", "127.0.0.1"),
        port=int(os.getenv("WEATHER_MAP_PORT", "8000")),
        default_grid_rows=int(os.getenv("WEATHER_MAP_DEFAULT_GRID_ROWS", "8")),
        default_grid_columns=int(os.getenv("WEATHER_MAP_DEFAULT_GRID_COLUMNS", "8")),
        max_grid_rows=int(os.getenv("WEATHER_MAP_MAX_GRID_ROWS", "20")),
        max_grid_columns=int(os.getenv("WEATHER_MAP_MAX_GRID_COLUMNS", "20")),
    )
